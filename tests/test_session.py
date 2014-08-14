import os
import sys

import unittest

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../src')
    import session
except ImportError:
    print "Please check the python PATH for import test module."
    exit(1)

class TestEventClass(unittest.TestCase):

	def setUp(self):
		self.e = session.Event()

	def tearDown(self):
		self.e = None

	def test_init(self):
		self.assertEqual(len(self.e.callbacks), 0)

	def test_on_emit(self):
		def cb(data):
			return data

		self.e.on(cb)
		self.assertEqual(self.e.callbacks[0], cb)
		self.assertEqual(self.e.emit(0), 0)

		self.e.on(cb)
		self.e.on(cb)
		self.e.on(cb)
		self.assertEqual(self.e.emit(0), [0,0,0,0])


class TestSessionClass(unittest.TestCase):

	def setUp(self):
		self.session = session.Session()

	def tearDown(self):
		self.session = None

	def test_init(self):
		self.assertEqual(self.session.age, 60)
		self.assertEqual(self.session.status, session.Status.READY)
		self.assertEqual(len(self.session.events), 0)

	def test_on_emit(self):
		status = None
		def cb(data):
			status = data
			print status
			return data

		def error_cb(data):
			self.assertEqual(data, session.Status.ERROR)

		self.session.on(session.Status.READY, cb)
		self.session.on(session.Status.RUNNING, cb)
		self.session.on(session.Status.SUCCESS, cb)
		self.session.on(session.Status.ERROR, error_cb)

		self.session.setStatus(session.Status.ERROR)
		#self.assertEqual(status, session.Status.ERROR)
		self.assertEqual(self.session.emit(session.Status.SUCCESS, "test_success"), "test_success")
		

class TestSessionsClass(unittest.TestCase):
	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_init(self):
		def done(error, result):
			print error
			print result

		mgr = session.Sessions()
		#s = session.Session(age=5)
		#mgr.add_session(s)


if __name__ == "__main__":
    unittest.main()
