from os import environ, listdir, path
from io import BytesIO
import queue
import shutil
import requests
import subprocess
import time
import threading
import yaml
from lib.diff import diff

from lib.log import logger
from lib.protocol import ERRResult, EXCResult, IGNResult, OKResult, Protocol, Result, TLEResult, Test, WAResult
from lib.util import get_key_value
from runners import get_runner, init_runners
from tasks import TaskInfo

def submit_results(task: TaskInfo, protocol: Protocol):
	logger.debug('Submitting protocol')
	result = protocol.generate()

	if not result:
		logger.error('Protocol creation failed')
		return

	response = requests.post(
		environ.get('UPLOAD_URL', 'http://localhost/problems/protocol_upload/'),
		data={
			'submit': task.submit_id
		},
		files={
			'protocol': ('protocol.xml', BytesIO(result))
		},
		headers={
			'X-Token': environ.get('TOKEN', 'token-insecure')
		}
	)

	if response.status_code != 200:
		logger.error(f'Could not upload response to server: {response.status_code}')
		logger.error(response.content)


def worker(running: threading.Event, queue: queue.Queue[TaskInfo]):
	logger.info('Starting worker thread')

	init_runners()

	isolate_exec = environ.get('ISOLATE_PATH', 'isolate')

	config_required_fields = ('memory', 'time')

	logger.debug('Cleaning up container')
	subprocess.run([isolate_exec, '--cleanup'], check=True)

	while running.is_set():
		if queue.empty():
			time.sleep(1)
			continue

		task = queue.get()

		try:
			runner = get_runner(task.language)

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
			p = subprocess.run([isolate_exec, '--init'], check=True, capture_output=True)
			box_path = path.join(p.stdout.decode().strip(), 'box')

			# Setup file
			with open(path.join(box_path, f'source.{task.language}'), 'w') as file:
				file.write(task.program)

			protocol = Protocol()

			# Compile if necessary
			if runner.info.compilation:
				runner.prepare_compile(box_path, f'source.{task.language}')

				compile_command = runner.compile(box_path, f'source.{task.language}')

				try:
					subprocess.run(compile_command, check=True, capture_output=True, cwd=box_path)

				except subprocess.CalledProcessError as e:
					logger.debug('Compilation error')
					protocol.add_compilation_log(e.stderr.decode() + e.stdout.decode())
					submit_results(task, protocol)

					logger.debug('Cleaning up container')
					subprocess.run([isolate_exec, '--cleanup'], check=True)

					continue

			# Get run command
			run_command = [
				isolate_exec,
				'-M-', # print to stdout
				'-iin',
				'-oout',
				f'-m {config["memory"] * 1024}',
				f'-t {config["time"]}',
				f'-w {config["wall-time"] if "wall-time" in config else config["time"] * 2}',
				f'-x {config["extra-time"] if "extra-time" in config else config["time"] * 1.2}',
				'--run',
				'--'
			]
			run_command.extend(runner.run(f'source.{task.language}'))

			runner.prepare_runtime(box_path)

			# Iterate all test cases
			tests_dir = path.join(task_dir, 'tests')
			for test_set in sorted(listdir(tests_dir)):
				# logger.debug(f'Set {test_set}')
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
					# logger.debug(f'Case {case}')

					shutil.copy(path.join(case_folder, f'{case}.in'), path.join(box_path, 'in'))

					p = subprocess.run(run_command, capture_output=True)

					meta = get_key_value(p.stdout.decode())

					if 'status' in meta:
						result: Result
						logger.debug('Not ok status')
						logger.debug(meta)
						logger.debug(p.stderr.decode())
						match meta['status']:
							case 'TO':
								result = TLEResult()
							case 'RE':
								result = EXCResult()
							case _:
								logger.warn(f'Got unexpected result: {meta["status"]}')
								result = ERRResult()

						protocol.add_test(Test(f'{test_set}.{case}', result, float(meta['time']) if 'time' in meta else 0))

					else:
						with open(path.join(case_folder, f'{case}.out'), 'r') as our_file, open(path.join(box_path, 'out'), 'r') as user_file:
							our_str, user_str = our_file.read(), user_file.read()


							if our_str == user_str:
								protocol.add_test(Test(f'{test_set}.{case}', OKResult(), float(meta['time'])))
								ignore_set = False
							else:
								protocol.add_test(Test(f'{test_set}.{case}', WAResult(), float(meta['time']), diff(our_str, user_str)))

				protocol.end_set(test_set)

			submit_results(task, protocol)

			logger.debug('Cleaning up container')
			subprocess.run([isolate_exec, '--cleanup'], check=True)

		except Exception:
			logger.exception('Exception occurred during task processing, ignoring task')





