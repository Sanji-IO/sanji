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



class Sanji(object):
	'''
	' This is for sanji framework.
	'''
	def __init__(self, role, ttl, hook, name, tunnel="temp", client_id="unknown", topic="sanji", resources=list(), 
		description="This is a example."):



class SanjiJSON(object):
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
		pass


		


class SanjiURI(object):
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

		pass





class Session(object):
	def __init__(self):
		pass



class ModelInitiator(object):
	'''
	'	Deal with some model initialization works like DB and Condifuration files creating.
	'''
	def __init__(self):
		pass

	def __del__(self):
		pass


class JsonDB(object):
	def __init__(self):
		pass



class Model2Model(object):
	def __init__(self):
		pass


