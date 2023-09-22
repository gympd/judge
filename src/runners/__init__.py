import importlib
import inspect
import os

from lib.log import logger

from runners.template import Runner

blacklisted_runners = ('__init__.py', 'template.py', 'example.py')

extensions: dict[str, Runner] = {}

def init_runners():
	logger.info('Initializing runners')

	for file in os.listdir(os.path.dirname(os.path.realpath(__file__))):
		if not file.endswith('.py') or file in blacklisted_runners:
			continue

		try:
			logger.info(f'Found {file}')

			module = importlib.import_module(f'.{file[:-3]}', 'runners')

			if not hasattr(module, 'init') or not callable(module.init):
				logger.error('Unable to load - init() is not function')
				continue


			runner = module.init()

			logger.info(f'  Language: {runner.info.language}')
			logger.info(f'  Extensions: {", ".join(runner.info.extensions)}')

			if not inspect.isclass(runner):
				logger.error('Unable to load - init() did not return class')
				continue

			r = runner()

			if not isinstance(r, Runner):
				logger.error('Unable to load - init() did returned class that does not inherit Runner class')
				continue

			for ext in r.info.extensions:
				extensions[ext] = r

		except Exception:
			logger.exception(f'Exception occured during loading of {file}')


def get_runner(extension: str):
	if extension in extensions:
		return extensions[extension]
	else:
		raise NotImplementedError