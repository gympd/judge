import shutil

from .template import Runner, RunnerInfo

class PythonRunner(Runner):
	info = RunnerInfo('Python', ['py'], False)

	@staticmethod
	def prepare_runtime(box_path: str):
		shutil.copy('/usr/bin/python3', box_path)

	@staticmethod
	def run(file: str) -> list[str]:
		return ['python3', file]

def init():
	return PythonRunner