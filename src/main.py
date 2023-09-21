import atexit
import queue
import signal
import threading

from lib.log import logger
from server import server
from worker import worker

logger.info('Starting judge')

task_queue = queue.Queue()

running = threading.Event()
running.set()

worker_thread = threading.Thread(target=worker, name="Worker", args=(running,task_queue))
worker_thread.start()

server_thread = threading.Thread(target=server, name="Server", args=(running,task_queue))
server_thread.start()

def handle_exit(*args):
	if not running.is_set():
		return

	logger.info('Judge stopping')

	running.clear()

	server_thread.join(30)
	worker_thread.join(30)

	logger.info('Judge stopped')

	# TODO: save current state, so that tasks can continue running

atexit.register(handle_exit)
signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)