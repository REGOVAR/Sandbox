#!env/python3
# coding: utf-8
import uuid
import os
import json
import aiohttp
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


rp = {}
def plugins_running():
	return rp.keys()





# SERVER IMPLEMENTATION

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




class RunHandler:
	def __init__(self):
		pass

	def up_status(self, request):
		pid      = request.match_info.get('pid', -1)
		name     = request.match_info.get('name', "?")
		progress = request.match_info.get('progress', -1)
		print("RunHandler[up_status] : taskid=" + pid + " name="+name + " : " + str(progress) )

		rp[pid] = (name, progress)

		msg = '{"action":"plugin_notify", "data" : [' + ','.join(['"' + str(k) + ':' + rp[k][0] + ' = ' + str(rp[k][1]) + '%"' for k in rp.keys()]) + ']}'
		notify_all(None, msg)

		return web.Response()


def notify_all(src, msg):
	for ws in app['websockets']:
		if src != ws[1]:
			ws[0].send_str(msg)



class AnalysisHandler:
	def __init__(self):
		pass

	def get(self, request):
		print ("GET analysis/")
		return web.Response(body=b"GET analysis/")

	async def post(self, request):
		data = await request.json()
		name = data["name"]
		fullpath = os.path.join(PLUGINS_DIR, name)
		config = data["config"]
		print ("POST analysis/ => ask celery to run task "+ str(name) + ", " + str(config))
		cw = execute_plugin.delay(fullpath, config)
		rp[cw.id] = (name, -1)


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
analysis = AnalysisHandler()
notif = RunHandler()


# Config server app
app = web.Application()
app['websockets'] = []
app.on_shutdown.append(on_shutdown) # on shutdown, close all websockets
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(TEMPLATE_DIR))


# Routes
app.router.add_route('GET',    '/www', website.home)
app.router.add_route('GET',    '/ws', websocket.get)

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

