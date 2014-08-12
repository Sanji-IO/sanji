import threading

class Status(object):
	READY = 0
	RUNNING = 1
	SUCCESS = 3
	ERROR = 4


class Event(object):
	def __init__(self):
		self.callbacks = list()

	def emit(self, data):
		result = list()
		map(lambda callback: result.append(callback(data)), self.callbacks)
		
		if len(result) == 1:
			return result[0]

		return result

	def on(self, callback):
		self.callbacks.append(callback)


class Session(object):

	def __init__(self, age=60):
		self.age = age
		self.status = Status.READY
		self.events = dict()

	def emit(self, name, data):
		event = self.events.get(name, None)
		if event == None:
			return
		return event.emit(data)
	
	def on(self, name, callback):
		event = self.events.get(name, Event())
		event.on(callback)
		self.events[name] = event

	def setStatus(self, status):
		self.status = status
		self.emit(self.status, self.status)

	def getStatus(self):
		return self.status


class Sessions(object):

	def __init__(self):
		self._sessionsLock = threading.Lock()
		self._sessions = list()

	def aging(self, tick=1):
		self._sessionsLock.acquire()
		removeSessionIndex = []
		timeoutCallbacks = []
		for index, session in enmurate(self._sessions):
			session.age = session.age - tick
			if session.age > 0:
				continue

			if session.getStatus() == False:
				session.setStatus(Status.ERROR)
				timeoutCallbacks.append(
					Thread(session.done, kwargs={ error: "Session Timeout"}))
			else:
				pass

			removeSessionIndex.append(index)

		# clean expired sessions
		for index in removeSessionIndex:
			del self._sessions[index]

		# executing timeout callbacks
		map(lambda thread: thread.start(), threads)
		map(lambda thread: thread.join(), threads)

		self._sessionsLock.release()


	def add_session(self, session):
		self._sessionsLock.acquire()
		self._sessions.append(session)
		self._sessionsLock.release()
