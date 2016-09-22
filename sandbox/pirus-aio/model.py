#!env/python3
# coding: utf-8
import os.path


from mongoengine import *
from bson.objectid import ObjectId




class User(Document):
	firstname = StringField(max_length=255)
	lastname  = StringField(max_length=255)
	email     = EmailField(max_length=255)
	is_admin  = BooleanField()

	def export_data(self):
		return {
			"firstname": self.firstname,
			"lastname" : self.lastname, 
			"is_admin" : self.is_admin,
			"email"    : self.email,
			"id": str(self.pk)
		}

	def import_data(self, data):
		try:
			self.firstname = data['firstname']
			self.lastname  = data['lastname']
			self.email     = data['email']
			self.is_admin  = data['is_admin']
		except KeyError as e:
			raise ValidationError('Invalid user: missing ' + e.args[0])
		return self

	@staticmethod
	def from_id(user_id):
		if not ObjectId.is_valid(user_id):
			return None;
		user = User.objects.get(pk=user_id)
		return user




class Pipeline(Document):
	name          = StringField(max_length=50, required=True)
	version       = StringField(max_length=10, required=True)
	description   = StringField(max_length=255)
	pirus_api_v   = StringField(max_length=10, required=True)
	path          = StringField(required=True)
	license       = StringField(max_length=50)
	input_allowed = ListField(StringField(max_length=10))
	developer     = StringField(max_length=100)
	
	def __str__(self):
		return self.path

	def export_data(self):
		return {
			"name" : self.name,
			"version" : self.version,
			"pirus_api_v" : self.pirus_api_v,
			"description" : self.description,
			"license" : self.license,
			"developer" : self.developer,
			"input_allowed" : self.input_allowed,
			"path": self.path, 
			"id": str(self.id)
		}

	def import_data(self, data):
		try:
			self.name          = data['name']
			self.version       = data['version']
			self.pirus_api_v   = data["pirus_api_v"]
			self.description   = data["description"]
			self.license       = data["license"]
			self.developer     = "" #str(data["developer"])
			self.input_allowed = data["input_allowed"]
			self.path          = data['path']
		except KeyError as e:
			raise ValidationError('Invalid pipeline: missing ' + e.args[0])
		return self 

	def get_qml(self):
		qml = None
		path = os.path.join(self.path, 'form.qml')
		if os.path.isfile(path):
			with open(path, 'r') as content_file:
				qml = content_file.read()
		return qml

	def get_config(self):
		conf = None
		path = os.path.join(self.path, 'config.default.json')
		if os.path.isfile(path):
			with open(path, 'r') as content_file:
				conf = content_file.read()
		return conf

	@staticmethod
	def from_id(pipe_id):
		if not ObjectId.is_valid(pipe_id):
			return None;
		pipe = Pipeline.objects.get(pk=pipe_id)
		return pipe

	@staticmethod
	def install(self, path_to_zip):
		# unzip
		# register in db
		pass


class Run(Document):
	pipe_id   = ObjectIdField(required=True)
	pipe_name = StringField(requiered=True)
	celery_id = StringField(required=True)
	user_id   = ObjectIdField()
	start     = StringField(required=True)
	end       = StringField()
	status    = StringField()
	inputs    = StringField()
	outputs   = StringField()
	prog_val  = StringField(required=True)
	prog_info = StringField()

	def export_data(self):
		return {
			"id" : str(self.id),
			"pipe_id" : str(self.pipe_id),
			"pipe_name" : self.pipe_name,
			"celery_id" : self.celery_id,
			"user_id": str(self.user_id), 
			"start": self.start,
			"end": self.end,
			"status": self.status,
			"inputs"  : self.inputs,
			"outputs" : self.outputs,
			"prog_val" : self.prog_val,
			"prog_info" : self.prog_info
		}

	def import_data(self, data):
		try:
			self.pipe_id   = data['pipe_id']
			self.pipe_name = data['pipe_name']
			self.celery_id = data['celery_id']
			self.user_id   = data['user_id']
			self.start     = data['start']
			self.status    = data['status']
			self.prog_val  = data['prog_val']
			if "end" in data:
				self.end = data['end']
			if "inputs" in data:
				self.inputs = data["inputs"]
			if "outputs" in data:
				self.outputs = data["outputs"]
			if "prog_info" in data:
				self.prog_info = data["prog_info"]
		except KeyError as e:
			raise ValidationError('Invalid plugin: missing ' + e.args[0])
		return self 

	@staticmethod
	def from_id(run_id):
		if not ObjectId.is_valid(run_id):
			return None;
		run = Run.objects.get(pk=run_id)
		return run

	@staticmethod
	def from_celery_id(run_id):
		run = Run.objects.get(celery_id=run_id)
		return run

