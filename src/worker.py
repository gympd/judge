import queue
import requests
import shutil
import subprocess
import threading
import time
import yaml
from io import BytesIO
from os import environ, listdir, path

from lib.diff import diff
from lib.log import logger
from lib.protocol import ERRResult, EXCResult, IGNResult, MLEResult, OKResult, Protocol, Result, Test, TLEResult, WAResult
from lib.util import get_key_value, smart_truncate
from runners import get_runner, init_runners
from tasks import TaskInfo


def submit_results(task: TaskInfo, protocol: Protocol):
	logger.debug('Submitting protocol')
	result = protocol.generate()

	if not result:
		logger.error('Protocol creation failed')
		return

	if 'OUTPUT_PROTOCOL_ONLY' in environ:
		logger.info(result)
		return

	response = requests.post(environ.get('UPLOAD_URL', 'http://localhost/problems/protocol_upload/'), data={'submit': task.submit_id}, files={'protocol': ('protocol.xml', BytesIO(result))}, headers={'X-Token': environ.get('TOKEN', 'token-insecure')})

	if response.status_code != 200:
		logger.error(f'Could not upload response to server: {response.status_code}')
		logger.error(response.content)


def worker(running: threading.Event, queue: queue.Queue[TaskInfo]):
	logger.info('Starting worker thread')

	init_runners()

	isolate_args = [environ.get('ISOLATE_PATH', 'isolate')]

	if 'CG_ENABLED' in environ:
		isolate_args.append('--cg')

	config_required_fields = ('memory', 'time')

	logger.debug('Cleaning up container')
	subprocess.run(isolate_args + ['--cleanup'], check=True)

	while running.is_set():
		if queue.empty():
			time.sleep(1)
			continue

		task = queue.get()

		try:
			try:
				runner = get_runner(task.language)
			except NotImplementedError:
				protocol = Protocol(-1, -1)
				protocol.add_compilation_log(
					f"""Ľutujeme, ale jazyk {task.language} zatiaľ nepodporujeme...
Ak si myslíš, že by sme tento jazyk mali podporovať, otvor Issue na:
https://github.com/gympd/judge/issues/new"""
				)

				submit_results(task, protocol)

				continue

			logger.info(f'Got submission for task {task.task_id} in {runner.info.language}')

			task_dir = path.join(environ.get('TASKS_DIR', '../data/problems'), task.task_id)
			if not path.isdir(task_dir):
				logger.warn('Problem not found, ignoring task')
				continue

			with open(path.join(path.abspath(task_dir), 'config.yml'), 'r') as file:
				config = yaml.safe_load(file)

				if not isinstance(config, dict):
					logger.error('Unable to load config file, ignoring task')
					continue

				ok = True

				for field in config_required_fields:
					if field not in config:
						logger.error(f'Missing field {field} in config')
						ok = False
						break

				if not ok:
					continue

			# Setup isolate
			logger.debug('Initializing container')
			p = subprocess.run(isolate_args + ['--init'], check=True, capture_output=True)
			box_path = path.join(p.stdout.decode().strip(), 'box')

			# Setup file
			with open(path.join(box_path, f'source.{task.language}'), 'w') as file:
				file.write(task.program)

			protocol = Protocol(config['time'], config['memory'])

			# Compile if necessary
			if runner.info.compilation:
				runner.prepare_compile(box_path, f'source.{task.language}')

				compile_command = isolate_args.copy()

				compile_command.extend(runner.compile_isolate_args)
				compile_command.extend(
					[
						'-M-',  # print to stdout
						'-oout',
						f'{"--cg-mem=" if "CG_ENABLED" in environ else "-m"}{runner.compile_limits.memory * 1024}',
						f'-t{runner.compile_limits.time}',
						f'-p{runner.compile_limits.processes}',
						'--run',
						'--',
					]
				)
				compile_command.extend(runner.compile(box_path, f'source.{task.language}'))

				p = subprocess.run(compile_command, capture_output=True)

				meta = get_key_value(p.stdout.decode())

				if 'status' in meta:
					logger.debug('Compilation error')

					with open(path.join(box_path, 'out'), 'r') as out_file:
						protocol.add_compilation_log(smart_truncate(out_file.read(), 4096))

					submit_results(task, protocol)

					logger.debug('Cleaning up container')
					subprocess.run(isolate_args + ['--cleanup'], check=True)

					continue

			# Get run command
			run_command = isolate_args.copy()

			run_command.extend(runner.run_isolate_args)
			run_command.extend(
				[
					'-M-',  # print to stdout
					'-iin',
					'-oout',
					f'{"--cg-mem=" if "CG_ENABLED" in environ else "-m"}{config["memory"] * 1024}',
					f'-t{config["time"]}',
					f'-w{config["wall-time"] if "wall-time" in config else config["time"] * 2}',
					f'-x{config["extra-time"] if "extra-time" in config else config["time"] * 1.2}',
					'--run',
					'--',
				]
			)
			run_command.extend(runner.run(f'source.{task.language}'))

			runner.prepare_runtime(box_path)

			# Iterate all test cases
			tests_dir = path.join(task_dir, 'tests')
			for test_set in sorted(listdir(tests_dir)):
				protocol.begin_set(test_set)

				testcases: list[str] = []

				case_folder = path.join(tests_dir, test_set)

				files = sorted(listdir(case_folder))

				for file in files:
					if file.endswith('.in'):
						case = file[:-3]
						if f'{case}.out' in files:
							testcases.append(case)
						else:
							logger.warn(f'Case {case} do not have output file, ignoring it')

				ignore_set = False

				for case in testcases:
					if ignore_set:
						protocol.add_test(Test(f'{test_set}.{case}', IGNResult(), 0))
						continue

					ignore_set = True

					shutil.copy(path.join(case_folder, f'{case}.in'), path.join(box_path, 'in'))

					p = subprocess.run(run_command, capture_output=True)

					meta = get_key_value(p.stdout.decode())

					logger.debug(meta)

					if 'cg-oom-killed' in meta:
						protocol.add_test(Test(f'{test_set}.{case}', MLEResult(), float(meta['time']) if 'time' in meta else 0, memory=int(meta['cg-mem']) if 'cg-mem' in meta else None))

					elif 'status' in meta:
						result: Result

						match meta['status']:
							case 'TO':
								result = TLEResult()
							case 'RE':
								result = EXCResult()
							case _:
								logger.warn(f'Got unexpected result: {meta["status"]}')
								result = ERRResult()

						protocol.add_test(Test(f'{test_set}.{case}', result, float(meta['time']) if 'time' in meta else 0, details=smart_truncate(p.stderr.decode(), 1024), memory=int(meta['cg-mem']) if 'cg-mem' in meta else None))

					else:
						with open(path.join(case_folder, f'{case}.out'), 'r') as our_file, open(path.join(box_path, 'out'), 'r') as user_file:
							our_str, user_str = our_file.read(), user_file.read()

							if our_str == user_str:
								protocol.add_test(Test(f'{test_set}.{case}', OKResult(), float(meta['time']), memory=int(meta['cg-mem']) if 'cg-mem' in meta else None))
								ignore_set = False
							else:
								protocol.add_test(Test(f'{test_set}.{case}', WAResult(), float(meta['time']), details=diff(our_str, user_str), memory=int(meta['cg-mem']) if 'cg-mem' in meta else None))

				protocol.end_set(test_set)

			submit_results(task, protocol)

			logger.debug('Cleaning up container')
			subprocess.run(isolate_args + ['--cleanup'], check=True)

		except Exception:
			logger.exception('Exception occurred during task processing, ignoring task')
