from os import environ
from typing import NamedTuple

from lib.xml_utils import dict_to_xml


class Result(object):
	code: int
	message: str
	description: str

	@staticmethod
	def get(code: str):
		# TODO: optimize
		for res in Result.__subclasses__():
			if res.code == code:
				return res

		raise NotImplementedError


class OKResult(Result):
	code = 1
	message = 'OK'
	description = 'Ok'


class WAResult(Result):
	code = 2
	message = 'WA'
	description = 'Wrong answer'


class TLEResult(Result):
	code = 3
	message = 'TLE'
	description = 'Time limit exceed'


class EXCResult(Result):
	code = 4  # maybe another id, idk
	message = 'EXC'
	description = 'Exception'


class MLEResult(Result):
	code = 5  # maybe another id, idk
	message = 'MLE'
	description = 'Memory limit exceed'


class ERRResult(Result):
	code = 6  # maybe another id, idk
	message = 'ERR'
	description = 'Internal error'


class IGNResult(Result):
	code = 7
	message = 'IGN'
	description = 'Ignored'


class Test(NamedTuple):
	name: str
	result: Result
	time: float
	memory: int | None = None
	details: str | None = None


class TaskLimits(NamedTuple):
	time: int
	memory: int


EXTENDED_PROTOCOL = 'EXTENDED_PROTOCOL' in environ


class Protocol:
	tests: list[Test] = []

	gradeable_sets = 0
	ok_sets = 0
	current_set_result = OKResult()
	result = OKResult()

	def __init__(self, time_limit: int, memory_limit: int) -> None:
		self.tests = []
		self.compile_log = None
		self.limits = TaskLimits(time_limit, memory_limit)

	compile_log: str | None = None

	def begin_set(self, name: str):
		if 'sample' not in name:
			self.gradeable_sets += 1
			self.current_set_result = OKResult()
		pass

	def end_set(self, name: str):
		if 'sample' not in name and isinstance(self.current_set_result, OKResult):
			self.ok_sets += 1

	def add_test(self, test: Test):
		self.tests.append(test)

		if not isinstance(test.result, OKResult):
			if isinstance(self.result, OKResult):
				self.result = test.result

			if isinstance(self.current_set_result, OKResult):
				self.current_set_result = test.result

	def add_compilation_log(self, log: str):
		self.compile_log = log

	def generate(self):
		score = 0 if self.gradeable_sets == 0 else int(self.ok_sets / self.gradeable_sets * 100)
		protocol: dict = {'runLog': {'test': [], 'score': score, 'details': f'Score: {score}', 'finalResult': self.ok_sets, 'finalMessage': f'{self.result.description} (OK: {score}%)'}}

		for test in self.tests:
			protocol['runLog']['test'].append(
				{
					'name': test.name,
					'resultCode': test.result.code,
					'resultMsg': test.result.message,
					'time': int(test.time * 1000),
					'memory': int(test.memory / 1024) if EXTENDED_PROTOCOL and test.memory is not None else None,
					'details': test.details,
				}
			)

		if self.compile_log:
			protocol['compileLog'] = self.compile_log

		if EXTENDED_PROTOCOL:
			protocol['limits'] = {'time': self.limits.time, 'memory': self.limits.memory}

		return dict_to_xml({'protokol': protocol})
