#!env/python3
# coding: utf-8 
import time
import requests
from celery import Celery, Task
import requests


app = Celery('tasks_manager')
app.conf.update(
    BROKER_URL = 'amqp://guest@localhost',
    CELERY_RESULT_BACKEND = 'rpc',
	CELERY_RESULT_PERSISTENT = False,

    CELERY_TASK_SERIALIZER = 'json',
    CELERY_ACCEPT_CONTENT = ['json'],
    CELERY_RESULT_SERIALIZER = 'json',
    CELERY_INCLUDE = [
        'tasks_manager'
    ],
    CELERY_TIMEZONE = 'Europe/Paris',
    CELERY_ENABLE_UTC = True,
)

class PirusTask(Task):
    """Task that sends notification on completion."""
    abstract = True

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        url = 'http://localhost:8888/notify'
        #data = {'clientid': kwargs['clientid'], 'result': retval}
        #requests.get('http://localhost:8888/notify/1/', data=data)

    def notify_progress(self, task_name, completion, info_label):
    	requests.get('http://localhost:8888/notify/task_id/MyPlugin/' + str(completion))




@app.task(base=PirusTask, queue='MyPluginQueue', bind=True)
def execute_plugin(self, name, config):
	print("[" + str(time.ctime()) + "] Worker : I execute the Plugin (from the queue MyPluginQueue) : " + name + " that will take " + str(config) + "s to be finish.")
	for i in range(0,10):
		time.sleep(5)
		self.notify_progress('MyPlugin', str(i*10), "")

	time.sleep(config)
	print("[" + str(time.ctime()) + "] Worker : OK job done for the Plugin : " + name + " that will take " + str(config) + "s to be finish.")

