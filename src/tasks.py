class TaskInfo:
	def __init__(self, tester_id: str, submit_id: str, user_id: str, task_id: str, language: str, priority: int, program: str):
		self.tester_id = tester_id
		self.submit_id = submit_id
		self.user_id = user_id
		self.task_id = task_id
		self.language = language
		self.priority = priority

		self.program = program
