#!env/python3
# coding: utf-8
import uuid
import os
import json
import aiohttp
import aiohttp_jinja2
import jinja2
import zipfile
import shutil

from aiohttp import web, MultiDict
from model import *
from mongoengine import *
from binascii import a2b_base64

from tasks_manager import execute_plugin 




# CONFIG
ERROR_ROOT_URL = "api.pirus.org/errorcode/"
PIRUS_API_V  = "1.0.0"
PLUGINS_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugins/")
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates/")
RUN_DIR      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs/")

''' creat/connect database '''
connect('pirus')


# CHECK 
if not os.path.exists(RUN_DIR):
	os.makedirs(RUN_DIR)
if not os.path.exists(PLUGINS_DIR):
	os.makedirs(PLUGINS_DIR)
if not os.path.exists(TEMPLATE_DIR):
	print("ERROR : Templates directory doesn't exists.", TEMPLATE_DIR)




# PIRUS FRAMEWORK

def fmk_rest_success(response_data=None, pagination_data=None):
	"""
		Build the REST success response that will encapsulate the given data (in python dictionary format)
		:param response_data: 	The data to wrap in the JSON success response
		:param pagination_data:	The data regarding the pagination
	"""
	if response_data is None:
		results = {"success":True}
	else:
		results = {"success":True, "data":response_data}
	if pagination_data is not None:
		results.update(pagination_data)
	return web.json_response(results)



def fmk_rest_error(message:str="Unknow", code:str="0", error_id:str=""):
	"""
		Build the REST error response
		:param message: 	The short "friendly user" error message
		:param code:		The code of the error type
		:param error_id:	The id of the error, to return to the end-user. 
							This code will allow admins to find in logs where exactly this error occure
	"""
	results = {
		"success":		False, 
		"msg":			message, 
		"error_code":	code, 
		"error_url":	ERROR_ROOT_URL + code,
		"error_id":		error_id
	}
	return web.json_response(results)



def fmk_check_pipeline_package(path:str):
	# files mandatory : plugin.py, form.qml, manifest.json, config.json
	# check manifest.json, mandatory fields :
	pass

def fmk_get_pipeline_forlder_name(name:str):
	cheked_name = ""
	for l in name:
		if l.isalnum() or l in [".", "-", "_"]:
			cheked_name += l
		if l == " ":
			cheked_name += "_"
	return cheked_name;


def plugins_available():
	return os.listdir(PLUGINS_DIR)


rp = {}
def plugins_running():
	return rp.keys()


def notify_all(src, msg):
	for ws in app['websockets']:
		if src != ws[1]:
			ws[0].send_str(msg)



# API HANDLERS

class WebsiteHandler:
	def __init__(self):
		pass

	@aiohttp_jinja2.template('home.html')
	def home(self, request):
		return {
			"cl" : list([ws[1] for ws in app['websockets']]), 
			"pr" : plugins_running(), 
			"pa" : plugins_available()
		}




class PipelineHandler:
	def __init__(self):
		pass

	def get(self, request):
		print ("GET pipeline/")
		return fmk_rest_success({"plugins" : plugins_available()})

	async def post(self, request):
		# 1- Retrieve pirus package from post request
		data = await request.post()
		ppackage = data['pipepck']
		# 2- save file into server plugins directory (with a random name to avoid problem if filename already exists)
		ppackage_name = str(uuid.uuid4())
		ppackage_path = os.path.join(PLUGINS_DIR, ppackage_name)
		ppackage_file = ppackage_path + ".zip"
		with open(ppackage_file, 'bw+') as f:
			f.write(ppackage.file.read())
		# 3- Unzip pipeline package
		os.makedirs(ppackage_path)
		zip_ref = zipfile.ZipFile(ppackage_file, 'r')
		zip_ref.extractall(ppackage_path)
		zip_ref.close()
		# 4- Check and clean module
		pdir  = ppackage_path
		if len(os.listdir(ppackage_path)) == 1 :
			pdir = os.path.join(ppackage_path, os.listdir(ppackage_path)[0])
		fmk_check_pipeline_package(pdir)
		data = json.load(open(os.path.join(pdir, 'manifest.json')))
		data.update({"path":os.path.join(PLUGINS_DIR, fmk_get_pipeline_forlder_name(data["name"]) + "_" + fmk_get_pipeline_forlder_name(data["version"]))})
		shutil.move(pdir, data["path"])
		# 5- Save pipeline into database
		pipeline = Pipeline()
		pipeline.import_data(data)
		pipeline.save()
		# 6- Clean directory and send OK response
		if (os.path.exists(ppackage_path)):
			shutil.rmtree(ppackage_path)
		os.remove(ppackage_file)
		return fmk_rest_success({"results": pipeline.export_data()})
		

	def delete(self, request):
		id = request.match_info.get('id', -1)
		print ("DELETE pipeline/<id=" + str(id) + ">")
		return web.Response(body=b"DELETE pipeline/<id>")

	def get_details(self, request):
		id = request.match_info.get('id', -1)
		if id == -1:
			return fmk_rest_error("Unknow pipeline id " + str(id))
		return fmk_rest_success({"results": Pipeline.objects.get(pk=id).export_data()})

	async def get_qml(self, request):
		id = request.match_info.get('id', -1)
		if id == -1:
			return fmk_rest_error("Id not found")
		pipeline = Pipeline.objects.get(pk=id)
		if pipeline is None:
			return fmk_rest_error("Unknow pipeline id " + str(id))
		qml = pipeline.get_qml()
		if qml is None:
			return fmk_rest_error("QML not found for the plugin " + str(id))
		return web.Response(
			headers=MultiDict({'Content-Disposition': 'Attachment'}),
			body=str.encode(qml)
		)

	def get_config(self, request):
		id = request.match_info.get('id', -1)
		if id == -1:
			return fmk_rest_error("Id not found")
		pipeline = Pipeline.objects.get(pk=id)
		if pipeline is None:
			return fmk_rest_error("Unknow pipeline id " + str(id))
		conf = pipeline.get_config()
		if conf is None:
			return fmk_rest_error("Config not found for the plugin " + str(id))
		return web.Response(
			headers=MultiDict({'Content-Disposition': 'Attachment'}),
			body=str.encode(conf)
		)



class RunHandler:
	def __init__(self):
		pass

	def get(self, request):
		print ("GET run/")
		return web.Response(body=b"GET run/")

	async def post(self, request):
		data = await request.json()
		name = data["name"]
		fullpath = os.path.join(PLUGINS_DIR, name)
		config = data["config"]
		print ("POST run/ => ask celery to run task "+ str(name) + ", " + str(config))
		cw = execute_plugin.delay(fullpath, config)
		rp[cw.id] = (name, -1)

		return web.Response(body=b"POST run/<name>/<config>")

	def delete(self, request):
		id = request.match_info.get('id', -1)
		print ("DELETE run/<id=" + str(id) + ">")
		return web.Response(body=b"DELETE run/<id>")

	def get_status(self, request):
		id = request.match_info.get('id', -1)
		print ("GET run/<id=" + str(id) + ">/status")
		return web.Response(body=b"GET run/<id>/status")

	def get_log(self, request):
		id = request.match_info.get('id', -1)
		print ("GET run/<id=" + str(id) + ">/log")
		return web.Response(body=b"GET run/<id>/log")

	def get_err(self, request):
		id = request.match_info.get('id', -1)
		print ("GET run/<id=" + str(id) + ">/err")
		return web.Response(body=b"GET run/<id>/err")

	def up_status(self, request):
		pid      = request.match_info.get('pid', -1)
		name     = request.match_info.get('name', "?")
		progress = request.match_info.get('progress', -1)
		print("RunHandler[up_status] : taskid=" + pid + " name="+name + " : " + str(progress) )

		rp[pid] = (name, progress)

		msg = '{"action":"plugin_notify", "data" : [' + ','.join(['"' + str(k) + ':' + rp[k][0] + ' = ' + str(rp[k][1]) + '%"' for k in rp.keys()]) + ']}'
		notify_all(None, msg)

		return web.Response()






class WebsocketHandler:
	async def get(self, request):

		peername = request.transport.get_extra_info('peername')
		if peername is not None:
			host, port = peername

		ws_id = "{}:{}".format(host, port)
		ws = web.WebSocketResponse()
		await ws.prepare(request)

		print('WS connection open by', ws_id)
		app['websockets'].append((ws, ws_id))
		print (len(app['websockets']))
		msg = '{"action":"online_user", "data" : [' + ','.join(['"' + _ws[1] + '"' for _ws in app['websockets']]) + ']}'
		notify_all(None, msg)
		print(msg)

		try:
			async for msg in ws:
				if msg.tp == aiohttp.MsgType.text:
					if msg.data == 'close':
						await ws.close()
					else:
						# Analyse message sent by client and send response if needed
						pass
				elif msg.tp == aiohttp.MsgType.error:
					print('ws connection closed with exception %s' % ws.exception())
		finally:
			print('WS connection closed for', ws_id)
			app['websockets'].remove((ws, ws_id))

		return ws


async def on_shutdown(app):
	for ws in app['websockets']:
		await ws[0].close(code=999, message='Server shutdown')





# LET'S GO, RUN SERVER

# handlers instances
websocket = WebsocketHandler()
website = WebsiteHandler()
runHdl = RunHandler()
pipeHdl = PipelineHandler()


# Config server app
app = web.Application()
app['websockets'] = []
app.on_shutdown.append(on_shutdown) # on shutdown, close all websockets
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(TEMPLATE_DIR))







# Routes
app.router.add_route('GET',    '/www', website.home)
app.router.add_route('GET',    '/ws', websocket.get)

app.router.add_route('GET',    '/pipeline', pipeHdl.get)
app.router.add_route('POST',   '/pipeline', pipeHdl.post)
app.router.add_route('DELETE', '/pipeline', pipeHdl.delete)
app.router.add_route('GET',    '/pipeline/{id}', pipeHdl.get_details)
app.router.add_route('GET',    '/pipeline/{id}/qml', pipeHdl.get_qml)
app.router.add_route('GET',    '/pipeline/{id}/config', pipeHdl.get_config)

app.router.add_route('GET',    '/run', runHdl.get)
app.router.add_route('POST',   '/run', runHdl.post)
app.router.add_route('GET',    '/run/{id}', runHdl.get_status)
app.router.add_route('GET',    '/run/{id}/status', runHdl.get_status)
app.router.add_route('GET',    '/run/{id}/log', runHdl.get_log)
app.router.add_route('GET',    '/run/{id}/err', runHdl.get_err)
app.router.add_route('GET',    '/run/{pid}/notify/{name}/{progress}', runHdl.up_status)






if __name__ == '__main__':
	web.run_app(app)	

