from .template import Runner, RunnerInfo

class CppRunner(Runner):
	info = RunnerInfo('C++', ['cpp', 'cc'], True)

	@staticmethod
	def compile(box_path: str, file: str) -> list[str]:
		return ['g++', '-static', '-O2', '-std=c++20', '-oexec', file]

	@staticmethod
	def run(file: str) -> list[str]:
		return ['exec']

def init():
	return CppRunner