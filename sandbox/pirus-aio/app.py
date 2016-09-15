#!env/python3
# coding: utf-8
import uuid
import os
import json
from aiohttp import web
import aiohttp_jinja2
import jinja2

from tasks_manager import execute_plugin 


PIRUS_API_V  = "1.0.0"
PLUGINS_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugins/")
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates/")


# PIRUS FRAMEWORK

def plugins_available():
	return os.listdir(PLUGINS_DIR)

def plugins_running():
	return []





# SERVER IMPLEMENTATION

class WebsiteHandler:
	def __init__(self):
		pass

	@aiohttp_jinja2.template('home.html')
	def home(self, request):
		return {
			"cl" : ["olivier", "sacha"], 
			"pr" : plugins_running(), 
			"pa" : plugins_available()
		}




class RunHandler:
	def __init__(self):
		pass

	def up_status(self, request):
		pid      = request.match_info.get('pid', -1)
		name     = request.match_info.get('name', "?")
		progress = request.match_info.get('progress', -1)
		print("RunHandler[up_status] : taskid=" + pid + " name="+name + " : " + str(progress) )

		return web.Response()






class AnalysisHandler:
	def __init__(self):
		pass

	def get(self, request):
		print ("GET analysis/")
		return web.Response(body=b"GET analysis/")

	async def post(self, request):
		data = await request.json()
		name = data["name"]
		config = data["config"]
		print ("POST analysis/ => ask celery to run task "+ str(name) + ", " + str(config))
		execute_plugin.delay(name, int(config))
		return web.Response(body=b"POST analysis/<name>/<config>")

	def delete(self, request):
		id = request.match_info.get('id', -1)
		print ("DELETE analysis/<id=" + str(id) + ">")
		return web.Response(body=b"DELETE analysis/<id>")

	def get_status(self, request):
		id = request.match_info.get('id', -1)
		print ("GET analysis/<id=" + str(id) + ">/status")
		return web.Response(body=b"GET analysis/<id>/status")

	def get_log(self, request):
		id = request.match_info.get('id', -1)
		print ("GET analysis/<id=" + str(id) + ">/log")
		return web.Response(body=b"GET analysis/<id>/log")

	def get_err(self, request):
		id = request.match_info.get('id', -1)
		print ("GET analysis/<id=" + str(id) + ">/err")
		return web.Response(body=b"GET analysis/<id>/err")




website = WebsiteHandler()
analysis = AnalysisHandler()
notif = RunHandler()


app = web.Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(TEMPLATE_DIR))


app.router.add_route('GET',    '/www', website.home)

app.router.add_route('GET',    '/analysis', analysis.get)
app.router.add_route('POST',   '/analysis', analysis.post)
app.router.add_route('DELETE', '/analysis/{id}', analysis.delete)
app.router.add_route('GET',    '/analysis/{id}', analysis.get_status)
app.router.add_route('GET',    '/analysis/{id}/status', analysis.get_status)
app.router.add_route('GET',    '/analysis/{id}/log', analysis.get_log)
app.router.add_route('GET',    '/analysis/{id}/err', analysis.get_err)

app.router.add_route('GET',    '/notify/{pid}/{name}/{progress}', notif.up_status)







if __name__ == '__main__':
	web.run_app(app)	

