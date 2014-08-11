#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import json
import sqlite3
import logging
import subprocess
import time

import os
path_root = os.path.abspath(os.path.dirname(__file__))

sys.path.append(path_root + "/../../lib/")

import sanji
from sanjilogger import *


CODE_OK = 200
CODE_BAD_REQUEST = 400
CODE_INTERNAL_SERVER_ERROR = 500

model_name = "template"

# Sanji's model profile (for MQTT usage)
sanji_profile = {
			"client_id": model_name,
			"tunnel": "/" + model_name,
			"name": model_name,
			"description": model_name,
			"resources": ["/system" + "/" + model_name],
			"role": "model",
			"ttl": 60,
			"hook": [],
		}


# Model's profile. (for Model usage)
model_profile = {
			"model_db": path_root + "/db/snmpd.json",
			"model_factory_db": path_root + "/db/snmpd.json",
		}

class Snmpd:
	def __init__(self, *args, **kwargs):
		# Model Profille
		self.sanji_profile = sanji_profile
		self.model_profile = model_profile

		# init()
		self.model_init()

		# Sanji's Callbacks
		self.mqttc = sanji.Sanji(**self.sanji_profile)
		self.mqttc.get_callback = self.get
		self.mqttc.post_callback = self.post
		self.mqttc.put_callback = self.put
		self.mqttc.delete_callback = self.delete

		self.mqttc.model_exit_callback = self.model_exit


		# touch pid file
		while self.mqttc.is_register_success != True:
			time.sleep(0.1)

		self.touch_pid_file(path_root + "/snmpd.pid")



	def get(self):
		'''
		' /network/snmpd
		'''		
		logger.debug("Snmpd.get()")
		logger.debug("Request JSON From: " + str(self.mqttc.json_obj.input_json))
		request_resource = self.mqttc.json_obj.input_json["resource"]
		request_resource_list = request_resource.split("/")

		# Validator: length
		if len(request_resource_list) != 3:
			self.mqttc.json_obj.assemble_error_response("Wrong resource length in request: %s" % request_resource)
			self.mqttc.publish_response(code=CODE_BAD_REQUEST)	
			return False		

		if request_resource_list[2] == "snmpd":
			self.get_row()
		else:
			self.mqttc.json_obj.assemble_error_response("Wrong resource in request: %s" % request_resource)
			self.mqttc.publish_response(code=CODE_BAD_REQUEST)	
			return False


	def post(self):
		self.mqttc.json_obj.assemble_error_response("No post function supported.")
		self.mqttc.publish_response(code=CODE_BAD_REQUEST)
		return False


	def put(self):
		'''
		' /network/snmpd
		'''				
		logger.debug("Snmpd.put()")
		logger.debug("Request JSON From: " + str(self.mqttc.json_obj.input_json))
		request_resource = self.mqttc.json_obj.input_json["resource"]
		request_resource_list = request_resource.split("/")
		# Validator(data): Need to have "data" field in request JSON
		if "data" not in self.mqttc.json_obj.input_json.keys():
			logger.debug("No data field in request JSON. Need by 'put'.")
			self.mqttc.json_obj.assemble_error_response("No data field in request JSON. Need by 'put'.")
			self.mqttc.publish_response(code=CODE_BAD_REQUEST)	
			return False
		
		# Validator(data.value): Need to have values of data field in request JSON
		if self.mqttc.json_obj.input_json["data"] == {}:
			logger.debug("No value of data field in request JSON. Need by 'put'.")
			self.mqttc.json_obj.assemble_error_response("No value of data field in request JSON. Need by 'put'.")
			self.mqttc.publish_response(code=CODE_BAD_REQUEST)	
			return False

		data = self.mqttc.json_obj.input_json["data"]

		if request_resource_list[2] == "snmpd":
			# /network/snmpd
			self.put_row()				
		else:
			self.mqttc.json_obj.assemble_error_response("Wrong resource in request: %s" % request_resource)
			self.mqttc.publish_response(code=CODE_BAD_REQUEST)	
			return False		



		

	def delete(self):
		self.mqttc.json_obj.assemble_error_response("No delete function supported.")
		self.mqttc.publish_response(code=CODE_BAD_REQUEST)
		return False

	def generate_new_db(self):
		# Check db/xxxxxx.db. If not, generate a new one.
		try:
			while True:
				file_size = os.path.getsize(self.model_profile["model_db"])
				if file_size == 0L:
					cmd = "rm %s" % self.model_profile["model_db"]
					subprocess.call(cmd, shell=True)							
					cmd = "sqlite3 %s < %s" % (self.model_profile["model_db"], self.model_profile["model_sql"])
					subprocess.call(cmd, shell=True)					
				else:
					break
					
				time.sleep(0.5)
		except:
			pass

		if os.path.isfile(self.model_profile["model_db"]) != True:
			cmd = "sqlite3 %s < %s" % (self.model_profile["model_db"], self.model_profile["model_sql"])
			subprocess.call(cmd, shell=True)

		cmd = "sync"
		subprocess.call(cmd, shell=True)		
		cmd = "sync"
		subprocess.call(cmd, shell=True)	


	def model_init(self):
		self.generate_new_db()
			
		self.model_db = SQL(model_profile["model_db"])

		# Check 'enable' bit.
		row = self.sql_get_row("snmpd", 1)
		if row["enable"] == 1:
			self.gen_snmpd_config(row)
			self.copy_snmpd_config_to_target()
			cmd = "snmpd -C -c /etc/snmp/snmpd.conf -Ln"
			process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
			start_ret = process.communicate()

			cmd = 'ps aux | grep "snmpd"'
			process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
			grep_ret = process.communicate()
			# find 'ps' string
			if grep_ret[0].find("/var/run/snmpd") != -1:
				logger.debug("Snmpd is running")
				self.sql_update_row("snmpd", ["currentStatus"], [1])	
				logger.info("Start snmpd successfully.(init)")



	def model_exit(self):
		pass




	# get()
	def get_row(self):
		'''
		'	/network/snmpd
		'''
		logger.debug("Snmpd.get_row()")
		request_resource = self.mqttc.json_obj.input_json["resource"]
		request_resource_list = request_resource.split("/")		
		table_name = request_resource_list[2]
		id = 1

		result = self.sql_get_row(table_name, id)
		if result != False:
			# assemble response JSON
			self.mqttc.json_obj.output_json["data"] = result
			self.mqttc.publish_response()
			return True 
		else:
			self.mqttc.json_obj.assemble_error_response("There is no data in this table")
			self.mqttc.publish_response(code=CODE_BAD_REQUEST)					
			return False


	# put()
	def put_row(self):
		'''
		' /network/snmpd
		'''
		logger.debug("Snmpd.put_row()")
		request_resource = self.mqttc.json_obj.input_json["resource"]
		request_resource_list = request_resource.split("/")
		table_name = request_resource_list[2]
		id = 1
		is_enable = self.mqttc.json_obj.input_json["data"]["enable"]

		result = self.sql_put_row(table_name, id)
		if result == True:
			self.sql_update_row("snmpd", ["modified"], [0])	
			self.mqttc.json_obj.output_json["data"]["modified"] = 0
			if is_enable == 1:
				self.gen_snmpd_config(self.mqttc.json_obj.input_json["data"])
				self.copy_snmpd_config_to_target()
				cmd = "killall snmpd"
				process = subprocess.call(cmd, shell=True)

				cmd = "snmpd -C -c /etc/snmp/snmpd.conf -Ln"
				process = subprocess.call(cmd, shell=True)

				cmd = 'ps aux | grep "snmpd"'
				process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
				grep_ret = process.communicate()
				# find 'ps' string
				if grep_ret[0].find("snmpd -C -c") != -1:
					logger.debug("Snmpd is running")
					self.sql_update_row("snmpd", ["currentStatus"], [1])	
					self.mqttc.json_obj.output_json["data"]["currentStatus"] = 1
					self.mqttc.publish_response()
					logger.info("Start snmpd successfully.")
					return True 

				else:
					self.sql_update_row("snmpd", ["currentStatus"], [0])	
					self.mqttc.json_obj.assemble_error_response("Snmpd start Failed")
					self.mqttc.publish_response(code=CODE_BAD_REQUEST)
					logger.info("Start snmpd failed.")
					return False

			else:
				cmd = "killall snmpd"
				process = subprocess.call(cmd, shell=True)
				self.sql_update_row("snmpd", ["currentStatus"], [0])	
				self.mqttc.json_obj.output_json["data"]["currentStatus"] = 0	
				self.mqttc.publish_response()
				logger.info("Stop snmpd successfully.")
				return True 
		else:
			self.mqttc.json_obj.assemble_error_response("There is no data in this table")
			self.mqttc.publish_response(code=CODE_BAD_REQUEST)
			return False



	# SQL - put #
	def sql_put_row(self, table_name, id):
		column_list = [x for x in self.mqttc.json_obj.input_json["data"].keys()]
		value_list = []
		for item in column_list:
			value_list.append(self.mqttc.json_obj.input_json["data"][item])
		logger.debug("value_list: " + str(value_list))
		arg_tuple = tuple(value_list)

		pair_string = self.model_db.generate_sql_update_argument_list(column_list)
		sql_command = "UPDATE %s SET %s WHERE id=%s" % (table_name, pair_string, id)
		rc = self.model_db.set(sql_command, arg_tuple) 
		if rc == False:
			self.mqttc.json_obj.assemble_error_response("SQL execute error: %s" % sql_command)
			self.mqttc.publish_response(code=CODE_BAD_REQUEST)	
			return False
		else:
			logger.debug(self.mqttc.json_obj.output_json)
			return True



	# SQL - Update row #
	def sql_update_row(self, table_name, column_list, value_list, row_id=1):
		arg_tuple = tuple(value_list)
		pair_string = self.model_db.generate_sql_update_argument_list(column_list)
		sql_command = "UPDATE %s SET %s WHERE id=%s" % (table_name, pair_string, row_id)
		#logger.debug("sql_command: ", str(sql_command))
		rc = self.model_db.set(sql_command, arg_tuple) 
		if rc == False:
			return False
		else:
			return True


	# SQL - get() #
	def sql_get_row(self, table_name, id):
		sql_schema_command = "PRAGMA TABLE_INFO(%s)" % table_name
		schema_result = self.model_db.select(sql_schema_command)	# tuple
		if schema_result == []:
			logger.debug("schema_result == []")
			return False
		
		sql_command = "SELECT * FROM %s WHERE id=%s" %  (table_name, id)

		try:
			data_result = list(self.model_db.select(sql_command)[0])	# tuple
		except sqlite3.OperationalError:
			logger.debug("sqlite3.OperationalError")
			return False
		except IndexError:
			logger.debug("IndexError")
			return False

		result_dict = dict()
		for i in range(0, len(schema_result)):
			result_dict[schema_result[i][1]] = data_result[i]

		return result_dict # {id: 1, interface: "eth0"}




	'''
    gb_file_append "agentAddress udp:${port}" ${SNMPD_FILE}
    gb_file_append "rocommunity \"${readCommunity}\"" ${SNMPD_FILE}
    gb_file_append "rwcommunity \"${readWriteCommunity}\" \"${trustHostIp}\"" ${SNMPD_FILE}
    gb_file_append "sysobjectid .1.3.6.1.4.1.8691.404.1.1" ${SNMPD_FILE}
    gb_file_append "syslocation Fl.4, No.135, Lane 235, Baoquao Rd., Xindian Dist., New Taipei City, Taiwan, R.O.C." ${SNMPD_FILE}
    gb_file_append "syscontact Moxa Inc., Embedded Computing Business." ${SNMPD_FILE}
	'''
	# Config Generator
	def gen_snmpd_config(self, data_dict):
		file = open(self.model_profile["snmpd_config"], "w")
		file.write("agentAddress udp:%s\n" % data_dict["port"])
		file.write("rocommunity %s\n" % data_dict["readCommunity"])
		file.write("rwcommunity %s %s\n" % (data_dict["writeCommunity"], data_dict["trustedIp"]))
		file.write("syslocation Fl.4, No.135, Lane 235, Baoquao Rd., Xindian Dist., New Taipei City, Taiwan, R.O.C.\n")
		file.write("syscontact Moxa Inc., Embedded Computing Business.\n")
		file.close()
		
	
	def copy_snmpd_config_to_target(self):
		cmd = "cp %s %s" % (self.model_profile["snmpd_config"], self.model_profile["snmpd_config_target_path"])
		subprocess.call(cmd, shell=True)


	def touch_pid_file(self, pid_file):
		pid = os.getpid()
		f = open(pid_file, "w")
		f.write(str(pid))
		f.close()	


if __name__ == '__main__':
	logger = SanjiLogger('MAR-2000', 'snmpd')
	snmpd = Snmpd()
	while True:
		time.sleep(60)

