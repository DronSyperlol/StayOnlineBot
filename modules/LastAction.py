from time import time as time_t

def time():
	return int(time_t())


#
#	Storage data = {
#		code: - last action code,
#		arg: - any data for it last action code
#		ts:	- end life timestamp
#	}
#

class LastAction:
	def __init__(self, lifeTime = 900):
		self.storage = {}
		self.lifeTime = lifeTime
		pass


	def set(self, key, code, argument = None):
		self.storage[key] = {}
		self.storage[key]["code"] = code
		self.storage[key]["arg"] = argument
		self.storage[key]["ts"] = time() + self.lifeTime
		pass
	

	def check(self, key):
		if (key in self.storage):
			if self.storage[key]['ts'] > time():
				return True
			del self.storage[key]
		return False
	
	
	def get(self, key):
		if (not key in self.storage):
			return None
		ret = {
			"code": self.storage[key]["code"],
			"arg": self.storage[key]["arg"]
		}
		del self.storage[key]
		return ret

	pass