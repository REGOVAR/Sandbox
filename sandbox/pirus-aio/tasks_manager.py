#!env/python3
# coding: utf-8 
import time
import requests
import shutil
import requests
import logging
import json
from celery import Celery, Task
from pluginloader import PluginLoader

# CONFIG
from config import *






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

    notify_url = ""
    run_path   = ""

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        #data = {'clientid': kwargs['clientid'], 'result': retval}
        #requests.get(NOTIFY_URL, data=data)
        pass

    def dump_context(self):
        print('  Context : Executing task id {0.id}, args: {0.args!r} kwargs: {0.kwargs!r}'.format(self.request))


    def notify_progress(self, task_name:str, completion:float, status:str=None, msg:str=None):
        data = { 
            "progress" : str(completion),
            "info" : task_name
        }
        requests.get(self.notify_url + "/" + str(completion))
        print ("send notify progress : ", self.notify_url)

    def notify_status(self, status:str):
        requests.get(self.notify_url + "/status/" + status)
        print ("send notify status : ", self.notify_url + "/status/" + status)

    def log_msg(self, msg:str):
        path = os.path.join(self.run_path, "out.log")
        print ("OUT.LOG", time.ctime(), msg)
        pass

    def log_err(self, msg:str):
        path = os.path.join(self.run_path, "err.log")
        print ("ERR.LOG", time.ctime(), msg)
        pass





@app.task(base=PirusTask, queue='MyPluginQueue', bind=True)
def execute_plugin(self, fullpath, config):
    self.run_path   = os.path.join(RUN_DIR, str(self.request.id))
    self.notify_url = NOTIFY_URL + str(self.request.id)
    self.notify_status("INIT")
    # 1- Create pipeline run directory
    try:
        shutil.copytree(fullpath, self.run_path)
        self.log_msg("Pipeline running environment created.")
    except:
        self.log_err("Failed to create pipeline running environment.")
        self.notify_status("FAILED")
        return 1
    # 2- Load pipeline instance
    try:
        loader = PluginLoader()
        # FIXME TODO : being able to load whole directory as plugin (not only one py file)
        # plugins = loader.load_directory(path=self.run_path, recursive=True)
        loader.load_directory(path=self.run_path, recursive=True)
        pluginInstance = loader.plugins['PirusPlugin']()
        pluginInstance.notify  = self.notify_progress
        pluginInstance.log_msg = self.log_msg
        pluginInstance.log_err = self.log_err
    except:
        self.log_err("Failed to load the pipeline ands instanciate the run.")
        self.notify_status("FAILED")
        return 2
    # 3- Run !
    try:
        self.notify_status("RUN")
        self.log_msg("Pipeline run ! GO.")
        self.dump_context()
        pluginInstance.run(config)
    except:
        self.log_err("Failed to create pipeline running environment.")
        self.notify_status("ERROR")
        return 3
    # 4- Done
    self.log_msg("Pipeline run done.")
    self.notify_status("DONE")
    return 0

