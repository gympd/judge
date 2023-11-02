import shutil
from os import environ

from .template import Runner, RunnerCompileLimits, RunnerInfo


class CppRunner(Runner):
	info = RunnerInfo('C++', ['cpp', 'cc'], True)

	compile_limits = RunnerCompileLimits(processes=5, memory=128)

	compile_isolate_args = [f'-EPATH={environ.get("PATH")}:/', '--stderr-to-stdout']

	@staticmethod
	def prepare_compile(box_path: str, source_path: str):
		shutil.copy(shutil.which('g++') or '/usr/bin/g++', box_path)
		shutil.copy(shutil.which('ld') or '/usr/bin/ld', box_path)

	@staticmethod
	def compile(box_path: str, file: str) -> list[str]:
		return ['g++', '-I/usr/include/c++/12/', '-I/usr/include/x86_64-linux-gnu/c++/12/', '-static', '-O2', '-std=c++20', '-oexec', file]

	@staticmethod
	def run(file: str) -> list[str]:
		return ['exec']


def init():
	return CppRunner
