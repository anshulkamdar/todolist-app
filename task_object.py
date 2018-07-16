class Task:
	def __init__(self, task, time_needed, priority):
		self.task = task
		self.time_needed = time_needed
		self.priority = priority

	def printdetails (self):
		print ('The task is: ' + self.task)
		print ('The time needed to complete this task is ' + self.time_needed)
		print ('The priority of this task from A(high) to C(low) is: ' + self.priority)

