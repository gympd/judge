import queue
import re
import socket
import threading

from lib.log import logger
from tasks import TaskInfo


def server(running: threading.Event, queue: queue.Queue[TaskInfo], host='0.0.0.0', port=12347):
	packet_pattern = re.compile(
		r'^(?P<protocol_version>[^\n]+)\n(?P<tester_id>[^\n]+)\n(?P<submit_id>[^\n]+)\n(?P<user_id>[^\n]+)\n(?P<task_id>[^\n]+)\n(?P<language>[^\n]+)\n(?P<priority>[^\n]+)\n(?P<magic_footer>magic_footer)\n(?P<program>[\s\S]+)$', re.MULTILINE
	)

	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	server.bind((host, port))

	server.listen()
	server.settimeout(1)

	logger.info('Started server')

	while running.is_set():
		try:
			(client, address) = server.accept()

			buffer = bytearray()

			packet = client.recv(1024)
			while packet:
				buffer.extend(packet)

				packet = client.recv(1024)

			data = buffer.decode('utf-8')
			match = re.fullmatch(packet_pattern, data)

			logger.info(f'Got connection from {address[0]}:{address[1]}')
			if match:
				queue.put(TaskInfo(match.group('tester_id'), match.group('submit_id'), match.group('user_id'), match.group('task_id'), match.group('language'), int(match.group('priority')), match.group('program')))
			else:
				logger.warn('Corrupt data received, discarding')

		except socket.timeout:
			pass
