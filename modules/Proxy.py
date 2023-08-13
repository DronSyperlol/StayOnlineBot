class Server:
	def __init__(self, proxy_info):
		self.is_active = True
		self.given_away = 0
		self.proxy_info = proxy_info
		pass
	pass


class Proxys:
	def __init__(self, proxy_path, limit_on_one_proxy = 5):
		self.servers = []
		self.iterator = 0
		self.proxy_path = proxy_path
		self.limit = limit_on_one_proxy
		pass


	def add(self, scheme: str, hostname: str, port: int | str, username: str = "", password: str = ""):
		self.rm(hostname)
		proxy_info = {
			"scheme": str(scheme),
			"hostname": str(hostname),
			"port": int(port),
			"username": str(username), 
			"password": str(password)
		}
		self.servers.append(Server(proxy_info))
		pass


	def rm(self, hostname):
		for server in self.servers:
			if (server.proxy_info["hostname"] == hostname):
				self.servers.remove(server)
				return True
		return False

	
	def get(self, deactive_also = False):
		if len(self.servers) <= 0:
			return None
		self.iterNext()
		if (not deactive_also):
			iterator = 0
			while (iterator < len(self.servers) and self.servers[self.iterPos()].is_active == False):
				self.iterNext()
		return self.servers[self.iterPos()].proxy_info


	def getFree(self, deactive_also = False) -> dict:
		if len(self.servers) <= 0:
			return None
		for index, server in enumerate(self.servers):
			if ((server.is_active or deactive_also) and server.given_away < self.limit):
				self.servers[index].given_away += 1
				return server.proxy_info
		return None


	def getUnpopular(self, deactive_also = False):
		if len(self.servers) <= 0:
			return None
		for index, server in enumerate(self.servers):
			if (server.is_active):
				selected_server = server
				self.iterSetPos(index)
				break
		for index, server in enumerate(self.servers):
			if ((server.is_active or deactive_also) and server.given_away < selected_server.given_away):
				selected_server = server
				self.iterSetPos(index)
		self.servers[self.iterPos()].given_away += 1
		return self.servers[self.iterPos()].proxy_info
		

	def getNext(self, prev_hostname):
		if len(self.servers) <= 0:
			return None
		for index, server in enumerate(self.servers):
			if (server.proxy_info["hostname"] == prev_hostname):
				self.iterSetPos(index)
				return self.get()
			pass
		return self.servers[self.iterPos()].proxy_info


	def getByHostname(self, hostname, deactive_also = False):
		if (not hostname):
			return None
		for server in self.servers:
			if (server.proxy_info["hostname"] == hostname):
				if (server.is_active or deactive_also):
					return server.proxy_info
				else:
					return None
			pass
		return None


	def exist(self, hostname):
		for server in self.servers:
			if (server.proxy_info["hostname"] == hostname):
				return True
		return False


	def haveFree(self, deactive_also = False):
		for server in self.servers:
			if (server.given_away < self.limit and (server.is_active or deactive_also)):
				return True
		return False
	

	def freeQuantity(self, deactive_also = False):
		total = len(self.servers) * self.limit
		for server in self.servers:
			if (server.is_active or deactive_also):
				total -= server.given_away
			else:
				total -= self.limit
		return 0 if (total < 0) else total


	def list(self) -> list | Server:
		return self.servers


	def is_empty(self):
		if (self.servers):
			return False
		return True
	
	def count(self, deactived_also = False) -> int:
		if (deactived_also):
			return len(self.servers)
		counter = 0
		for server in self.servers:
			if (server.is_active):
				counter += 1
		return counter
	

	def incrementPopularity(self, hostname):
		for index, server in enumerate(self.servers):
			if (server.proxy_info["hostname"] == hostname):
				self.servers[index].given_away += 1
				return True
		return False
	
	def decrementPopularity(self, hostname):
		for index, server in enumerate(self.servers):
			if (server.proxy_info["hostname"] == hostname):
				self.servers[index].given_away -= 1
				return True
		return False


	def setPopularity(self, hostname, value):
		for index, server in enumerate(self.servers):
			if (server.proxy_info["hostname"] == hostname):
				self.servers[index].given_away = value
				return True
		return False
		
	def setPopularityAll(self, value):
		for i in range(len(self.servers)):
			self.servers[i].given_away = value


	def setActivity(self, hostname, status = True):
		for index, server in enumerate(self.servers):
			if (server.proxy_info["hostname"] == hostname):
				self.servers[index].is_active = status
				return True
		return False



	#
	#	Iterator:
	#
	def iterSetPos(self, value):
		self.iterator = value
		pass

	def iterPos(self):
		return self.iterator
	
	def iterNext(self):
		self.iterator += 1
		if (self.iterator >= len(self.servers)):
			self.iterator = 0

	def iterBack(self):
		self.iterator -= 1
		if (self.iterator < 0):
			self.iterator = len(self.servers) - 1




	def load(self):
		from json import load
		try:
			with open(self.proxy_path) as f:
				temp = load(f)
		except:
			return False
		for server in temp:
			if ("username" in server):
				if ("password" in server):
					self.add(server["scheme"], server["hostname"], server["port"], server["username"], server["password"])
				else:
					self.add(server["scheme"], server["hostname"], server["port"], server["username"])
			else:
				self.add(server["scheme"], server["hostname"], server["port"])
		return True

	def save(self):
		from json import dump
		temp = []
		self.iterSetPos(0)
		for _ in range(len(self.servers)):
			temp.append(self.get())
		with open(self.proxy_path, 'w') as f:
			dump(temp, f)
		pass


	def parseText(self, text, limit = 10000, change_on = None):
		data = text.split('\n')
		loaded_servers = 0
		for row in data:
			row = row.replace("\n", "")
			row = row.replace("\t", "")

			if (len(row) < 1):
				continue

			comment_index = row.find("#")
			if (comment_index > 0):
				row = row[:comment_index]
			elif (comment_index == 0):
				continue

			row = row.replace(' ', ':')
			splited_row = row.split(':')
			
			if (len(splited_row) < 3):
				continue
				
			if (limit <= loaded_servers):
				break

			loaded_servers += 1
			if (change_on):
				self.rm(change_on)
				
			if (len(splited_row) == 4):
				self.add(splited_row[0], splited_row[1], splited_row[2], splited_row[3])
				continue

			if (len(splited_row) == 5):
				self.add(splited_row[0], splited_row[1], splited_row[2], splited_row[3], splited_row[4])
				continue

			self.add(splited_row[0], splited_row[1], splited_row[2])
			pass	
		return loaded_servers

	

	pass
