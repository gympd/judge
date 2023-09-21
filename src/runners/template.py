class RunnerInfo:
	def __init__(self, language: str, extensions: list[str], compilation: bool) -> None:
		self.language = language
		self.extensions = extensions
		self.compilation = compilation

class Runner:
	info: RunnerInfo

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
