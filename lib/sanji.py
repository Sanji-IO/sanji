#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import mosquitto
import json
import time
import copy
import logging
import sys
import sqlite3
import glob
import inspect 	# for debug frame
import os

from router import *
from random import randint
from threading import Thread
from threading import Lock
from datetime import datetime


path_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(path_root + '/../')
from sanjilogger import *


sanjiMutex = Lock()
deregMutex = Lock()
regMutex = Lock()

# Parameter Example
'''
	model_profile = {
		"client_id": "",
		"tunnel": "",
		"name": "",
		"description": "",
		"resources": [],
		"role": "",
		"ttl": 0,
		"hook": [],
	}
'''

CODE_OK = 200
CODE_BAD_REQUEST = 400
CODE_INTERNAL_SERVER_ERROR = 500


try:
	broker_ip = os.environ['BROKER_IP']
except:
	broker_ip = "127.0.0.1"

try:
	broker_port = int(os.environ['BROKER_PORT'])
except:
	broker_port = 1883

class Sanji:
	'''
	' This is for sanji framework.
	'''
	def __init__(self, role, ttl, hook, name, tunnel="temp", client_id="unknown", topic="sanji", resources=list(), 
		description="This is a example."):

		self.controller_topic = "/controller"	# Send req/rsp to controller
		self.temp_topic = tunnel	# just for listening
		self.topic = tunnel	# just for listening		
		self.register_topic = ""
		self.deregister_topic = ""
		self.message_id = 0
		self.qos = 2
		self.ip = broker_ip
		self.port = broker_port
		self.name = name # Model Name for Registration. It will add in controller's DB.
		self.description = description
		self.resources = resources
		self.role = role
		self.ttl = ttl
		self.hook = hook
		self.broker_retry_times = 100

		self.pid = os.getpid()
		if role == "model":
			self.client_id = "m" + "/" + str(self.name) + "/" + str(self.pid)
		else:
			self.client_id = "v" + "/" + str(self.name) + "/" + str(self.pid)
		
		self.mq = mosquitto.Mosquitto(client_id=self.client_id[0:23])
		self.mq.on_connect = self.on_connect
		self.mq.on_message = self.on_message
		self.mq.on_publish = self.on_publish
		self.mq.on_subscribe = self.on_subscribe

		self.msg_payload = ""
		self.register_json = dict()
		self.deregister_json = dict()
		self.json_obj = JSON(self.name)
		self.uri_obj = URI(self.name)
		self.get_callback = None
		self.post_callback = None
		self.put_callback = None
		self.delete_callback = None
		self.hook_callback = None
		self.model_init_callback = None
		self.model_exit_callback = None
		self.response_callback = None
		self.is_register_success = False
		self.is_connect = False
		self.logger = SanjiLogger('MAR-2000', self.name)


		self.sanji_lock = False

		# Session Handler
		self.session = Session()

		# Sanji Registration
		self.register_status = 1 		# 1: initial, 0: OK, -1: Fail
		self.deregister_status = 1 		# 1: initial, 0: OK, -1: Fail
		
		self.connect_broker(self.port)
		self.thread = self.thread_mqtt_loop()	
		self.sanji_registration()




	def sanji_registration(self):
		self.logger.info("sanji_registration()")
		self.registration_manager()



	def connect_broker(self, port=1883):
		'''
		' Use MQTT's API to connect broker
		'''
		self.logger.info("connect broker")
		i = 0
		while i < self.broker_retry_times and self.is_connect != True:
			try:
				self.logger.info("start to connect broker")
				ret = self.mq.connect(self.ip, port, keepalive=566)
				self.logger.info("end to connect broker, ret = %s" % ret)
			except Exception as e:
				print "eeeeeeeeeee------------------>", e
				i += 1
				time.sleep(1)
				continue

			break

		self.mq.subscribe(self.topic, 2)
		



	def generate_id(self):
		'''
		'
		'''
		#self.logger.debug("Sanji.generate_id()")
		self.message_id = randint(10000, 99999999)
		#self.logger.debug(":::::::::::::::::" + str(self.message_id) + ":::::::::::::::::::::")
		return self.message_id


	def aging(self):
		while True:
			for key in self.queue.keys():
				aging_time = self.queue[key][2]
				self.queue[key][2] -= 1
				if self.queue[key][2] < 0:
					#print "delete %s" % key
					del self.queue[key]
			time.sleep(1)



	def is_id_in_session(self, target_id):
		for item in self.session.queue:
			id = item[0]
			if id == target_id:
				return True

		return False

	def deregister_sanji(self, tunnel):
		'''
		' [Unfinished]
		' disconnect Sanji's Controller
		'''
		# block, unitl deregister_sanji callback is fired.
		deregMutex.acquire() 

		self.logger.debug("Sanji.deregister_sanji()")
		self.mq.subscribe(self.deregister_topic, 2)
		self.deregister_json["id"] = self.generate_id()
		self.deregister_json["method"] = "delete"
		self.deregister_json["resource"] = "/controller/registration/" + str(self.name)
		self.deregister_json["tunnel"] = tunnel

		if self.ttl < 60:
			ttl = 60
		else:
			ttl = self.ttl

		self.session.add(self.deregister_json["id"], [self.callback_deregister_sanji, self.callback_fail_deregister_sanji, ttl])
		logger.debug("self.session.queue: %s" % str(self.session.queue))
		self.publish_request(json_dict=self.deregister_json)
		self.logger.info("Deregister Sanji controller... end")


	def callback_deregister_sanji(self):
		'''
		'
		'''
		self.logger.debug("Sanji.callback_deregister_sanji()")
		self.deregister_status = 0
		self.mq.unsubscribe(self.deregister_topic)
		self.is_register_success = False
		self.logger.info("Deregister Sanji controller OK. Model Name :::::::::: %s ::::::::::" % self.name)

		# release for registration_manager
		deregMutex.release()

		#calling Model's model_exit()
		if self.model_exit_callback:
			self.model_exit_callback()



	def callback_fail_deregister_sanji(self):
		'''
		'
		'''
		self.logger.debug("Sanji.callback_fail_deregister_sanji()")
		self.logger.info("Deregister Sanji controller Failed.")
		self.mq.unsubscribe(self.deregister_topic)
		self.deregister_status = -1
		self.logger.info(self.json_obj.input_json["code"])
		self.logger.info(self.json_obj.input_json["data"])

		# release for registration_manager
		deregMutex.release()


	def register_sanji(self, tunnel):
		'''
		' [Unfinished]
		' Connect Sanji's Controller
		'
		'''
		# block, unitl register_sanji callback is fired.
		regMutex.acquire()

		self.logger.debug("Sanji.register_sanji()")
		self.mq.subscribe(self.register_topic, 2)
		self.register_json["id"] = self.generate_id()
		self.register_json["method"] = "post"
		self.register_json["resource"] = "/controller/registration"
		self.register_json["tunnel"] = tunnel
		self.register_json["data"] = dict()
		self.register_json["data"]["name"] = self.name
		self.register_json["data"]["description"] = self.description
		self.register_json["data"]["resources"] = self.resources
		self.register_json["data"]["role"] = self.role
		self.register_json["data"]["ttl"] = self.ttl
		self.register_json["data"]["hook"] = self.hook
		self.logger.debug("My id is %s" % self.register_json["id"])
		if self.ttl < 60:
			ttl = 60
		else:
			ttl = self.ttl		
		self.session.add(self.register_json["id"], [self.callback_register_sanji, self.callback_fail_register_sanji, ttl])
		self.publish_request(json_dict=self.register_json)
		self.logger.info("Register Sanji controller...")



	def callback_register_sanji(self):
		'''
		'
		'''
		self.logger.debug("Sanji.callback_register_sanji()")
		self.register_status = 0
		self.topic = self.json_obj.input_json["data"]["tunnel"]
		try:
			self.topic = str(self.topic)
		except:
			pass
		self.logger.debug("Controller gives me the topic: %s" % self.topic)
		self.mq.unsubscribe(self.register_topic)
		self.mq.subscribe(self.topic, self.qos)
		self.is_register_success = True
		self.logger.info("Register Sanji controller OK. Model Name :::::::::: %s ::::::::::" % self.name)

		# write tunnel to /home/log/tunnel.log file
		try:
			os.system('mkdir -p /home/log')
			with open('/home/log/tunnel.log', 'a') as f:
				f.write('%s\t%s\t%s\n' % (
						datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
						self.name, self.topic
					)
				)
		except Exception as e:
			sys.exit(1)
			raise e

		# release for registration_manager
		regMutex.release()

	def callback_fail_register_sanji(self):
		'''
		'
		'''
		self.logger.debug("Sanji.callback_fail_register_sanji()")
		self.logger.info("Register Sanji controller Failed.")
		self.mq.unsubscribe(self.register_topic)
		self.register_status = -1

		# release for registration_manager
		regMutex.release()




	def registration_manager(self):
		'''
		' Handle the retry of registration.
		'''
		self.logger.debug("registration_manager()")
		self.register_status = 1 		# 1: initial, 0: OK, -1: Fail
		self.deregister_status = 1 		# 1: initial, 0: OK, -1: Fail


		ret = False
		# handle deregister()
		retry_times = 200
		self.deregister_topic = str(self.generate_id())
		self.deregister_sanji(self.deregister_topic)
		while deregMutex.acquire() and retry_times > 0:
			retry_times -= 1	
			deregMutex.release()
			if self.deregister_status == 0:
				ret = True
				break
			elif self.deregister_status == -1:
				logger.debug("self.deregister_status: %s" % self.deregister_status)
				self.deregister_status = 1
				self.deregister_sanji(self.deregister_topic)
			else:
				logger.debug("self.deregister_status: %s" % self.deregister_status)

			time.sleep(1)

		# handle register()
		retry_times = 200
		self.register_topic = str(self.generate_id())
		self.register_sanji(self.register_topic)
		while regMutex.acquire() and retry_times > 0:
			retry_times -= 1
			regMutex.release()
			if self.register_status == 0:
				ret = True
				break
			elif self.register_status == -1:
				logger.debug("self.register_status: %s" % self.register_status)
				self.register_status = 1
				self.register_sanji(self.register_topic)
			else:
				logger.debug("self.register_status: %s" % self.register_status)

			time.sleep(1)

		return ret
	


	def on_disconnect(self, mosq, userdata, rc):
		self.logger.debug("--------------------------------------------->[on_disconnect]")


	def on_connect(self, mosq, obj, rc):
		self.logger.debug("--------------------------------------------->[on_connect]")
		self.logger.debug("rc: " + str(rc))
		self.logger.debug("mosq: " + str(mosq))
		self.logger.debug("obj: " + str(obj))
		self.is_connect = True
		self.mq.subscribe(self.topic, 2)
		

	def on_publish(self, mosq, obj, mid):
		self.logger.debug("--------------------------------------------->[on_publish]")
		#self.logger.debug("MQTT mid: " + str(mid))
		

	def on_subscribe(self, mosq, obj, mid, granted_qos):
		self.logger.debug("--------------------------------------------->[on_subscribe]")
		#self.logger.debug("Subscribed: " + str(mid) + " " + str(granted_qos))
		

	def on_unsubscribe(self, mosq, obj, mid):
		self.logger.debug("--------------------------------------------->[on_unsubscribe]")
		#self.logger.debug("Subscribed: " + str(mid))


	def on_message(self, mosq, obj, msg):
		self.logger.debug("[on_message]")
		
		#self.logger.debug("topic = " + msg.topic)
		#self.logger.debug("\npayload = \n" + str(msg.payload))
		#self.logger.debug("Message ID = %d" % msg.mid)
		#self.logger.debug("length = %d" % len(msg.payload))
		#self.logger.debug("QoS Level = %d" % msg.qos)
		self.msg_payload = str(msg.payload)


		sanjiMutex.acquire()
		parsing_rc = self.json_obj.parsing_json(self.msg_payload)
		if parsing_rc == "response":
			sanjiMutex.release()
			self.json_obj.parsing_response()
			if self.json_obj.sanji_response_is_valid == True:
				if self.json_obj.input_json["code"] == CODE_OK:
					self.logger.debug("Response Code is %s" % CODE_OK)
					self.session.session_handler(self.json_obj.input_json["id"], 0)
				elif self.json_obj.input_json["code"] == CODE_BAD_REQUEST:
					self.logger.debug("Response Code is %s" % CODE_BAD_REQUEST)
					self.session.session_handler(self.json_obj.input_json["id"], -1)
				elif self.json_obj.input_json["code"] == CODE_INTERNAL_SERVER_ERROR:
					self.logger.debug("Response Code is %s" % CODE_INTERNAL_SERVER_ERROR)
					self.session.session_handler(self.json_obj.input_json["id"], -1)
				else:
					self.logger.debug("Unknown response code %s" % self.json_obj.input_json["code"])
					self.session.session_handler(self.json_obj.input_json["id"], -1)				
			else:
				self.json_obj.assemble_error_response("sanji_response_is_valid == False")
				self.publish_response(code=CODE_INTERNAL_SERVER_ERROR)	

		elif parsing_rc == "request":
			self.json_obj.parsing_request()

			if self.json_obj.sanji_request_is_valid == True:
				self.logger.debug("sanji_request_is_valid == True")

				# Parse URI	
				self.logger.debug(self.json_obj.input_json["resource"])
				if self.uri_obj.parse_uri(self.json_obj.input_json["resource"]) == False:
					self.json_obj.assemble_error_response("Wrong resource field in JSON.")
					self.publish_response(code=CODE_BAD_REQUEST)

				# Select "method" function to use.
				do_method = {
						"post": self.post,
						"get": self.get,
						"put": self.put,
						"delete": self.delete
				}
				method = self.json_obj.input_json["method"].lower()
				# TODO(aeluin) a empty data is not required
				if not self.json_obj.output_json.has_key("data"):
					self.json_obj.output_json["data"] = dict()
				if method not in do_method.keys():
					self.logger.debug(self.json_obj.input_json)
					self.json_obj.assemble_error_response("KeyError: No such method to use: %s" % method)
					self.publish_response(code=CODE_BAD_REQUEST)
				else:
					thread = Thread(target=do_method[method])
					thread.daemon = True
					thread.start()
					#do_method[method]()
					
			else:
				self.logger.debug("sanji_request_is_valid == False")
			
		elif parsing_rc == "hook":
			self.json_obj.parsing_request()
			if self.hook_callback:
				self.hook_callback()
			else:
				self.json_obj.assemble_error_response("No hook() callback to call...")
				self.publish_response(code=CODE_BAD_REQUEST)				

		else:
			self.logger.debug("parsing json failed")
			sanjiMutex.release()
			
	def on_log(self, mosq, obj, level, string):
		self.logger.debug("[on_log]")
		self.logger.debug(string)


	def get(self):
		'''
		' READ
		'''
		self.logger.debug("Sanji.get()")
		if self.get_callback:
			self.get_callback()


	def post(self):
		'''
		' CREATE/INSERT
		'''
		self.logger.debug("Sanji.post()")
		if self.post_callback:
			self.post_callback()


	def put(self):
		'''
		' UPDATE, use d.has_key() to avoid empty keys.
		'''
		self.logger.debug("Sanji.put()")
		if self.put_callback:
			self.put_callback()


	def delete(self):
		'''
		' DELETE, use d.has_key() to avoid empty keys./
		'
		' 
			{
				"id":3,
				"method":"DELETE",
				"resource": "/networks/ethernets/1",
				"code": 200, (... The code is only for response)
			}
		'
		'
		'''
		self.logger.debug("Sanji.delete()")
		if self.delete_callback:
			self.delete_callback()	


	def publish_error(self, code, message, log=None):
		self.json_obj.assemble_error_response(message, log)
		self.publish_response(code=code)

	def publish_request(self, data=False, json_dict=False, topic=False):
		'''
		' Just publish the JSON to controller.
		' You should assemble your JSON before calling this function.
		'''
		self.logger.debug("Sanji.publish_request()")

		if topic == False:
			topic = self.controller_topic		

		if json_dict == False:
			output_json = self.json_obj.output_json
		else:
			output_json = json_dict
		
		if data != False:
			output_json["data"] = data
		elif data == None:
			del output_json["data"]

		if output_json.has_key("code"):
			del output_json["code"]
		

		json_string = json.dumps(output_json)
		ret = self.mq.publish(topic, json_string, self.qos)
		self.logger.debug("Sanji.publish_request() end: %s" % str(ret))


	def publish_response(self, code=CODE_OK, data=False, json_dict=False, topic=False):
		'''
		' Just publish the JSON to controller.
		' You should assemble your JSON before calling this function.
		'''
		self.logger.debug("Sanji.publish_response(), code= %s" % code)



		if topic == False:
			topic = self.controller_topic

		if json_dict == False:
			output_json = self.json_obj.output_json
		else:
			output_json = json_dict
		
		if data == None:
			del output_json["data"]
		elif data != False:
			output_json["data"] = data

		output_json["code"] = code
		code = int(code)
		if code >= 400:
			try:
				output_json["data"]["message"]
				self.logger.warning(output_json["data"]["message"])
			except KeyError, e:
				self.logger.warning('You should put error messsage in response!')
				output_json["data"] = dict(message = "Unknown error. Please contact your system administrator.")
		try:
			output_json["sign"].append(self.name)
		except:
			output_json["sign"] = list()
			output_json["sign"].append(self.name)	

		json_string = json.dumps(output_json)
		
		# Sync to Flash Memory
		try:
			if output_json["method"] in ("put", "post", "delete"):
				os.system("sync")				
		except:
			logger.debug("json has no key: 'method'")
			pass


		self.mq.publish(topic, json_string, self.qos)
		try:
			sanjiMutex.release()
		except:
			logger.info("Someone release this key 2 times... oops")

		self.logger.debug("Sanji.publish_response() OK")



	def publish(self, json_dict=False, topic=False):
		'''
		' Just publish the JSON to controller.
		' You should assemble your JSON before calling this function.
		'''
		self.logger.debug("Sanji.publish()")
		if json_dict == False:
			json_dict = self.json_obj.output_json
		json_string = json.dumps(json_dict)
		#self.logger.debug(json_string)
		if topic == False:
			topic = self.controller_topic

		self.mq.publish(topic, json_string, self.qos)
		try:
			sanjiMutex.release()
		except:
			logger.info("Someone release this key 2 times... oops")

	def Router(self):
		'''
		' Get Router instance.
		' User could use this function to get a Router with current
		' sanji instance.
		'''
		return Router(self)

	def start_mqtt(self, loop_interval=1):
		'''
		' Start the MQTT listening. 
		' When this function is called, it will step into infinite loop.
		'''
		self.logger.info("Start Model OK. Waiting for request.")
		self.mq.loop_forever()


	def stop_mqtt(self):
		self.deregister_status = 1
		self.deregister_topic = str(self.generate_id())
		self.mq.subscribe(self.deregister_topic, 2)
		self.deregister_sanji(self.deregister_topic)

		# do not wait, just exist
		time.sleep(1)
		#while self.deregister_status != 0: pass

		self.mq.disconnect()
		self.thread.join()
		self.logger.info("Model stopped.") 

	def thread_mqtt_loop(self):
		t = Thread(target=self.start_mqtt)
		t.daemon = True
		t.start()
		return t


	def receive_signal(signum, stack):
	    #print '-------->Received:', signum
		#calling Model's model_exit()
		if self.model_exit_callback:
			self.model_exit_callback()




class JSON:
	'''
	' Provide JSON operations.
	' Format Example:
		{
			"id":3,
			"method":"get",
			"resource": "/services",
			"code": 200,
			"data": {
				"resources":["http_server","dhcp_server"]
			}
		}
	'''
	def __init__(self, model_name):
		self.input_json_is_valid = False
		self.sanji_request_is_valid = False
		self.sanji_response_is_valid = False
		self.init_json = dict()
		self.input_json = dict()
		self.output_json = dict()
		self.name = model_name
		self.logger = SanjiLogger('MAR-2000', self.name)

	def parsing_json(self, raw_json):
		'''
		' Parsing if the json file is valid
		'''
		#self.logger.debug("JSON.parsing_json()")
		self.input_json_is_valid = False
		#self.logger.debug(raw_json)

		try:
			self.init_json = json.loads(raw_json)
		except ValueError, TypeError:
			self.logger.warning("ValueError: json's format error.")
			return "failed"

		if "code" in self.init_json:
			# response json
			return "response"
		elif "sign" in self.init_json:
			return "hook"
		else:
			# request json
			return "request"


	def parsing_request(self):
		'''
		' Parsing the request.
		' If it is correct, set the sanji_request_is_valid flag to 'True'
		'''
		self.logger.debug("JSON.parsing_request()")
		self.input_json = copy.deepcopy(self.init_json)
		self.input_json_is_valid = True	
		self.output_json = copy.deepcopy(self.init_json)	# Prepare the response json
		self.output_json["code"] = CODE_OK			# default 200			

		self.sanji_request_is_valid = False

		# 1. Valid Sanli's format
		if self.input_json.has_key("id") == False:
			self.logger.debug("Wrong JSON request: No 'id' field")
			self.assemble_error_response(CODE_BAD_REQUEST, "Wrong JSON request: No 'id' field")
			return False

		if self.input_json.has_key("method") == False:
			self.logger.debug("Wrong JSON request: No 'method' field")
			self.assemble_error_response(CODE_BAD_REQUEST, "Wrong JSON request: No 'method' field")
			return False

		if self.input_json.has_key("resource") == False:
			self.logger.debug("Wrong JSON request: No 'resource' field")
			self.assemble_error_response(CODE_BAD_REQUEST, "Wrong JSON request: No 'resource' field")
			return False

		self.sanji_request_is_valid = True
		return True



	def parsing_response(self):
		'''
		' Parsing the response JSON after the request.
		'''
		self.logger.debug("JSON.parsing_response()")
		self.input_json = copy.deepcopy(self.init_json)
		self.input_json_is_valid = True	
		self.output_json = copy.deepcopy(self.init_json)	# Prepare the response json
		self.output_json["code"] = CODE_OK			# default 200			

		self.sanji_response_is_valid = False		
		# 1. Valid Sanji's format
		if self.input_json.has_key("id") == False:
			self.logger.debug("Wrong JSON response: No 'id' field")
			self.assemble_error_response(CODE_BAD_REQUEST, "Wrong JSON response: No 'id' field")
			return False
		if self.input_json.has_key("code") == False:
			self.logger.debug("Wrong JSON response: Response has the 'code' field")
			self.assemble_error_response(CODE_BAD_REQUEST, "Wrong JSON response: No 'code' field")
			return False		

		#if self.input_json.has_key("data") == False:
		#	self.logger.debug("Wrong JSON response: Response has the 'data' field")
		#	self.assemble_error_response(CODE_BAD_REQUEST, "Wrong JSON response: No 'data' field")
		#	return False	

		self.logger.debug("sanji_response_is_valid")
		self.sanji_response_is_valid = True
		return True



	def assemble_error_response(self, message, log = None):
		'''
		' Remove original data.
		' Use data error message to replace.
		'''
		self.output_json["data"] = dict()
		frameinfo = inspect.getframeinfo(inspect.currentframe())
		message = message + " @" +  str(inspect.currentframe().f_back.f_lineno)
		self.output_json["data"]["message"] = message
		if log:
			self.output_json["data"]["log"] = log
		


class URI:
	'''
	' Provide URI operations.
	' We could use URI parser to parsing uri in resources.
	'''
	def __init__(self, model_name):
		self.resource_dict = {"index": "", 			# 7
								"full_name": "", 	# /network/ethernet
								"full_uri": "", 	# /network/ethernet/7
								"short_name": "", 	# /ethernet
							}

		self.name = model_name
		self.logger = SanjiLogger('MAR-2000', self.name)

	def validate_uri(self, resource_uri):
		'''
		' Validate if the format of resource URI is correct.
		'''
		if resource_uri == "":
			return False
		return True

	def parse_uri(self, resource_uri):
		'''
		' Parse the resource URI and store the information into "resource_dict".
		'''
		if self.validate_uri(resource_uri) != True:
			return False
		temp_list = resource_uri.split('/')
		try:
			temp_list.remove("")
		except ValueError:
			pass

		try:
			index = int(temp_list[-1])
		except:
			index = "" 	# Capability Case

		self.resource_dict["index"] = index
		self.resource_dict["full_uri"] = resource_uri
		if index == "":
			# /network/ethernet
			self.resource_dict["short_name"] = "/" + temp_list[-1]
			self.resource_dict["full_name"] = resource_uri
		else:
			# /network/ethernet/7
			try:
				self.resource_dict["short_name"] = "/" + temp_list[-2]
			except:
				self.resource_dict["short_name"] == ""
				return False

			self.resource_dict["full_name"] = ""
			for i in temp_list[:-1]:
				self.resource_dict["full_name"] += "/" + i

		return True


	def parse_route_uri(self, resource_uri):
		'''
		' Deal with complex model
		'''
		if self.validate_uri(resource_uri) != True:
			return False



class Session:
	def __init__(self):
		# Queue:  [[success_callback, fail_callback, 60], [...], ...]
		self.queue = dict()
		self.run_aging_daemon()


	def add(self, id, session_list):
		'''
		' Ex: [foo, 60]
		'''
		self.queue[id] = session_list


	def aging(self):
		while True:
			for key in self.queue.keys():
				aging_time = self.queue[key][2]
				self.queue[key][2] -= 1
				if self.queue[key][2] < 0:
					#print "delete %s" % key
					# call fail_callback function due to TTL timeout
					self.queue[key][1]()
					del self.queue[key]
			time.sleep(1)
		
	def session_handler(self, id, status):
		# Queue:  [[success_callback, fail_callback, 60], [...], ...]
		'''
		' id: session ID 
		' status: 0: success; -1: failed
		'''
		for key in self.queue.keys():
			if key == id:
				if status == 0:
					callback = self.queue[key][0]
				else:
					callback = self.queue[key][1]

				if callback:
					callback()

				del self.queue[key]
				return

		print "----------------------------------------> This is NOT my response. MID: %s. Drop it!!" % id
		print "----------------------------------------> This is NOT my response. MID: %s. Drop it!!" % id
		print "----------------------------------------> This is NOT my response. MID: %s. Drop it!!" % id
 
	def run_aging_daemon(self):
		t = Thread(target=self.aging)
		t.daemon = True
		t.start()




class ModelInitiator(object):
	'''
	'	Deal with some model initialization works like DB and Condifuration files creating.
	'''
	def __init__(self):
		pass

	def __del__(self):
		pass