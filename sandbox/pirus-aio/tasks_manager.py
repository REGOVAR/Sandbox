#!env/python3
# coding: utf-8 
import time
import requests
from celery import Celery, Task
import requests
from pluginloader import PluginLoader


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

    def dump_context(self):
        print('  Context : Executing task id {0.id}, args: {0.args!r} kwargs: {0.kwargs!r}'.format(self.request))


    def notify_progress(self, task_name, completion, info_label):
        requests.get('http://localhost:8080/notify/' + str(self.request.id) +'/' + task_name + '/' + str(completion))





@app.task(base=PirusTask, queue='MyPluginQueue', bind=True)
def execute_plugin(self, fullpath, config):
    print(time.ctime(), fullpath, "Start execute plugin")

    # 1- Try to import plugin
    loader = PluginLoader()
    #plugins = loader.load_directory(path=fullpath, recursive=True)
    loader.load_directory(path=fullpath, recursive=True)
    pluginInstance = loader.plugins['PirusPlugin']()
    pluginInstance.notify = self.notify_progress
    print(time.ctime(), fullpath, "Loading plugin done")


    try:
        print(time.ctime(), fullpath, "Run plugin")
        self.dump_context()
        pluginInstance.run(config)
    except:
        print(time.ctime(), fullpath, "ERROR !!")

    print(time.ctime(), fullpath, "Finish")

