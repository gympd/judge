class RunnerInfo:
	def __init__(self, language: str, extensions: list[str], compilation: bool) -> None:
		self.language = language
		self.extensions = extensions
		self.compilation = compilation


class RunnerCompileLimits:
	def __init__(self, time: float = 10, memory: int = 256, processes: int = 1) -> None:
		self.time = time
		self.memory = memory
		self.processes = processes


class Runner:
	info: RunnerInfo
	compile_limits = RunnerCompileLimits()
	compile_isolate_args: list[str] = []
	run_isolate_args: list[str] = []

	@staticmethod
	def prepare_compile(box_path: str, source_path: str):
		pass

	@staticmethod
	def compile(box_path: str, file: str) -> list[str]:
		raise NotImplementedError

	@staticmethod
	def prepare_runtime(box_path: str):
		pass

	@staticmethod
	def run(file: str) -> list[str]:
		raise NotImplementedError
