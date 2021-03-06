



# http://docs.celeryproject.org/en/latest/getting-started/first-steps-with-celery.html
sudo apt install rabbitmq-server
sudo pip3 install tornado celery

sudo pip3 install celery aiohttp aiohttp_jinja2 pluginloader


# Run Celery (in a new shell)
celery worker -A tasks_manager --loglevel=info -Q MyPluginQueue

# Run server (in a new shell)
python3 app.py

# [Tornado] Test run from api (in a new shell)
curl "http://localhost:8888/run/MyPlugin/9"
# [aioHTTP] Test run from api (in a new shell)
curl "http://localhost:8080/www"
curl "http://localhost:8080/analysis/1/log"
curl --data '{"name":"MyPlugin", "config": 9}'  "http://localhost:8080/analysis"


# Test run from python 
ipython3
 > from tasks_manager import execute_plugin
 > r = execute_plugin.delay("Toto", 180)
 > r.status
 > ...



