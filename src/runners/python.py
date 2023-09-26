import shutil
from os import environ

from .template import Runner, RunnerCompileLimits, RunnerInfo


class PythonRunner(Runner):
	info = RunnerInfo('Python', ['py'], True)

	compile_limits = RunnerCompileLimits(processes = 8, memory = 64)

	# Fix python runner in docker container
	run_isolate_args = [environ.get('PYTHON_ISOLATE_ARGS', '-ELD_LIBRARY_PATH=/lib:/usr/lib:/usr/local/lib:/lib/x86_64-linux-gnu:/usr/local/lib/python3.11')]

	@staticmethod
	def prepare_compile(box_path: str, source_path: str):
		ruff_exec = environ.get('RUFF_EXECUTABLE_PATH', shutil.which('ruff') or '/usr/bin/ruff')
		shutil.copy(ruff_exec, box_path)

	@staticmethod
	def compile(box_path: str, file: str) -> list[str]:
		return ['ruff', file]

	@staticmethod
	def prepare_runtime(box_path: str):
		python_exec = environ.get('PYTHON_EXECUTABLE_PATH', shutil.which('python3') or '/usr/bin/python3')
		shutil.copy(python_exec, box_path)

	@staticmethod
	def run(file: str) -> list[str]:
		return ['python3', file]

def init():
	return PythonRunner