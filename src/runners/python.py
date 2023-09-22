import shutil
from os import environ

from .template import Runner, RunnerInfo


class PythonRunner(Runner):
	info = RunnerInfo('Python', ['py'], False)
	isolate_args = [environ.get('PYTHON_ISOLATE_ARGS', '-ELD_LIBRARY_PATH=/lib:/usr/lib:/usr/local/lib:/lib/x86_64-linux-gnu:/usr/local/lib/python3.11')]

	@staticmethod
	def prepare_runtime(box_path: str):
		shutil.copy(environ.get('PYTHON_EXECUTABLE_PATH', '/usr/bin/python3'), box_path)


	@staticmethod
	def run(file: str) -> list[str]:
		return ['python3', file]

def init():
	return PythonRunner