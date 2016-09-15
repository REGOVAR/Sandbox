#!env/python3
# coding: utf-8
import uuid
import os
from tornado import websocket, web, ioloop
import json
from tasks_manager import execute_plugin 


PIRUS_API_V = "1.0.0"
PLUGINS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugins/")


print(PLUGINS_DIR)

cl = []
pr = []


def plugins_available():
	return os.listdir(PLUGINS_DIR)

def plugins_running():
	return pr




class IndexHandler(web.RequestHandler):
	def get(self):
		self.render("index.html", plugins_available=plugins_available, plugins_running=plugins_running, cl=cl)


class PluginNotificationHandler(web.RequestHandler):
	def get(self, pid, task_name, completion):
		self.finish()
		print("PluginNotificationHandler : taskid=" + pid + " name="+task_name + " : " + str(completion) )


class PluginRunHandler(web.RequestHandler):
	def get(self, plugin_name, config):
		print("RunHandler : " + str(plugin_name) + ", " + str(config))
		execute_plugin.delay(plugin_name, int(config)	)

		# Notify all connected users
		for c in cl:
			c.write_message('{"action":"plugin_state", "data" : "'+plugin_name+'"}')


class SocketHandler(websocket.WebSocketHandler):
	def check_origin(self, origin):
		return True

	def on_message(self, message):
		for c in cl:
			print(str(c))

		print (str(message))
		data = json.loads(message)

		if data["action"] == "authent":
			print ('Authent action : return user session token and ask him to give us client info')
			self.write_message('{"action":"authent", "data" : '+ str(uuid.uuid4()) + '}')

	def open(self):
		if self not in cl:
			print("OPEN " + str(self))
			cl.append(self)

	def on_close(self):
		if self in cl:
			print("CLOSE " + str(self))
			cl.remove(self)



class ApiHandler(web.RequestHandler):
	@web.asynchronous
	def get(self, *args):
		self.finish()
		id = self.get_argument("id")
		value = self.get_argument("value")
		data = {"id": id, "value" : value}
		data = json.dumps(data)
		for c in cl:
			c.write_message(data)

	@web.asynchronous
	def post(self):
		pass











app = web.Application([
	(r'/', IndexHandler),
	(r'/ws', SocketHandler),
	(r'/api', ApiHandler),
	(r'/run/(\w+)/(\d+)', PluginRunHandler), 
	(r'/notify/(\w+)/(\w+)/(\d+)', PluginNotificationHandler), 
	(r'/(favicon.ico)', web.StaticFileHandler, {'path': '../'}),
	(r'/(rest_api_example.png)', web.StaticFileHandler, {'path': './'}),
	])
web.URLSpec

if __name__ == '__main__':
	app.listen(8888)
	ioloop.IOLoop.instance().start()

