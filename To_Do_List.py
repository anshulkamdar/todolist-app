from __future__ import print_function
from task_object import Task
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from datetime import datetime
from datetime import date
from datetime import time
from datetime import timedelta
import pytz
import datetime
import pprint
import dateutil.parser


###########################################################################################################
# Function to return a list of free intervals in the day given the list of busy intervals
def get_free_intervals (busy_intervals):

	free_intervals = []
	today = date.today()
	# Wake and sleep time for checking for free intervals within it
	eastern = pytz.timezone ('US/Eastern')

	wake_time = eastern.localize(datetime.datetime(today.year, today.month, today.day, 5, 30))
	sleep_time = eastern.localize(datetime.datetime(today.year, today.month, today.day, 22, 30))

	# Fill in the free interval with correct timings of start and end

	if busy_intervals == []:
		free_intervals.append({'start': wake_time.isoformat(), 'end': sleep_time.isoformat()})
		return free_intervals

	start_time = wake_time.isoformat()
	end_time = sleep_time.isoformat()
		
	iterations = 0
	while (start_time != end_time):
		# Compare start time with the chronological interval at the time
		# Conditional statement if you are FREE AT THE START TIME
		if iterations >= len(busy_intervals):
			free_start = busy_intervals[iterations-1]['end']
			free_end = end_time
		
		elif start_time < busy_intervals[iterations]['start']:
			# If nothing is scheduled at or earlier than the wake up time, then you have the information to create a free interval
			free_start = start_time
			free_end = busy_intervals[iterations]['start']
		
		# Conditional statement if you are not FREE AT THE START TIME
		elif busy_intervals[iterations]['start'] <= start_time:
			# If you are not free at the start time, then you have the information for when you're free interval will start
			free_start = busy_intervals[iterations]['end']
			try:
				# Last piece of a free interval is either the beginning of the NEXT busy interval
				free_end = busy_intervals[iterations + 1]['start']
			except IndexError:
				# If there is no other interval, then you are technically free until your end time
				free_end = end_time
		
		start_time = free_end
		free_intervals.append({'start': free_start, 'end': free_end})
		iterations += 1
	return free_intervals		

##############################################################################################################
# Returns a sorted list of task_objects by priority given the original unsorted task objects
def priority_sort_tasks (task_objects):
	
	# BUBBLE SORT TO SORT TASK_OBJECTS
	for i in range(len(task_objects)-1, 0, -1):
		for j in range(i):
			if task_objects[j+1].priority < task_objects[j].priority:
				task_objects[j+1], task_objects[j] = task_objects[j], task_objects[j+1]
	return task_objects

#####################################################################################
################################ MAIN PROGRAM #######################################
#####################################################################################

# Setup the Google Calendar API
SCOPES = 'https://www.googleapis.com/auth/calendar'
store = file.Storage('credentials.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('calendar', 'v3', http=creds.authorize(Http()))


# Reads input from a text to get tasks, time needed, and priority
# Format from text file looks like: TASK:TN:PRI(A/B/C)
task_objects = []
with open ('tasks.txt', 'rt') as tasks_file:
	contents = tasks_file.readlines()
	for line in contents:
		if line != '\n':
			task_string, task_time, task_priority = line.split(":")
			task_objects.append(Task(task_string, task_time, task_priority))


today = date.today()

# Wake and sleep time for checking for free intervals within it
eastern = pytz.timezone ('US/Eastern')
wake_time = eastern.localize(datetime.datetime(today.year, today.month, today.day, 5, 30))
sleep_time = eastern.localize(datetime.datetime(today.year, today.month, today.day, 22, 30))

body = {"timeMin": wake_time.isoformat(),
	"timeMax": sleep_time.isoformat(),
	"timeZone": 'US/Eastern',
	"items": [{"id": 'anshulkamdar@gmail.com'}]
	}
 

sorted_task_objects = priority_sort_tasks(task_objects)
tomorrow_file = open('tomorrow.txt', 'w')

######################################################
#################### CREATE EVENTS ###################
######################################################
# Create algorithm that automatically creates an events and updates the free interval as it does it	
for i in range(len(sorted_task_objects)):
	availability = service.freebusy().query(body=body).execute()
	busy_intervals = availability['calendars']['anshulkamdar@gmail.com']['busy']
	free_intervals = get_free_intervals(busy_intervals)
	if (free_intervals == []):
		print ("There is no free time to schedule any tasks in your day. Sorry!")
		break
	for interval in free_intervals:
		start_interval = dateutil.parser.parse(interval['start'])
		end_interval = dateutil.parser.parse(interval['end'])
		interval_gap = ((end_interval - start_interval) / timedelta(minutes=1))
		if (float(sorted_task_objects[i].time_needed)) <= interval_gap:
			print ('Scheduling your task...')

			print ('Start time:' + str(start_interval.isoformat()))
			end_time = start_interval + datetime.timedelta(minutes = int(sorted_task_objects[i].time_needed))
			print ('End time:' + str(end_time.isoformat()))

			event = {'summary': sorted_task_objects[i].task,
				'start': {'dateTime': start_interval.isoformat(),
					'timeZone': 'America/New_York'},
				'end': {'dateTime': (start_interval + datetime.timedelta(minutes=int(sorted_task_objects[i].time_needed))).isoformat(),
					'timeZone': 'America/New_York'},
				'reminders': {'useDefault': True}}
			event = service.events().insert(calendarId='primary', body=event).execute()
			print ('Event created')
		elif (float(sorted_task_objects[i].time_needed)) > interval_gap:
			print ('Not enough time in interval to fit this task in. Will put into Tomorrow.txt file')
			# PUT REST OF TASKS INTO TOMORROW FILE
			tomorrow_file.write (sorted_task_objects[i].task + ':' + str(sorted_task_objects[i].time_needed) + ':' + sorted_task_objects[i].priority)

