#	+-----------------------------------------------------------+
#	|	Developer:	Syperlol aka Dron aka DronSyperlol			|
#	|	Contacts:	t.me/Syperlol github.com/DronSyperlol		|
#	|															|
#	+-----------------------------------------------------------+



import mysql.connector as mysql
import asyncio
from time import time



#	Consts:
WAIT_AFTER_QUERY_SECS = 0.5
COMMAND_FOR_CHECK_CONNECTION = "SELECT * FROM `users` WHERE `user_id` = 0"
CHECK_CONNECTION_TIMEOUT = 2 * 600 	#	20 mins



class Pool:
	def __init__(self, host, port, user, password, database, instances = 5):
		self.connections = []
		self.query_per_sec = 0
		self.query_per_min = 0
		self.__query_stat_start__ = time()
		self.__query_stat_counter__ = 0

		self.__host__ = host
		self.__port__ = port
		self.__user__ = user
		self.__password__ = password
		self.__database__ = database
		self.__instances__ = instances
		
		for _ in range(instances):
			con = mysql.connect(host=host, port=port, user=user, password=password, database=database)
			curs = con.cursor()
			connection = {
				"connection": con,
				"cursor": curs,
				# "result": None,
				"is_free": True,
				"last_executing": 0
			}
			self.connections.append(connection)
			pass
		pass
		
		
	async def execute(self, command, args = None):
		self.__increment_and_update_query_stat__()
		if args == None:
			return await self.__execute__(command)
		
		command = await self.__parse_command__(command, args)
		return await self.__execute__(command)
		

	async def __execute__(self, command):
		attemps = 20
		result = None

		while attemps > 0:
			for index, connection in enumerate(self.connections):
				if (connection["is_free"] and connection["last_executing"] < time() + WAIT_AFTER_QUERY_SECS):
					self.connections[index]["is_free"] = False
					try:
						connection["cursor"].execute(command)
						result = connection["cursor"].fetchall()
						connection["connection"].commit()
					except Exception as e:
						print(f"DATABASE EXCEPTION\n{e}\n===============\nQuery: {command}")
						pass
					self.connections[index]["last_executing"] = time()
					self.connections[index]["is_free"] = True
					return result
			print("All connections busy, waiting free")
			attemps -= 1
			await asyncio.sleep(1)
			pass
		return None


	async def __parse_command__(self, string: str, args):
		#	 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36
		#	"S E L E C T   *   F R  O  M     t  a  b  l  e     W  H  E  R  E     c  o  l  u  m  n     =     ?  ;  "						args = 5

		#	"SELECT * FROM table WHERE column = ?"						args = 5
		#	"SELECT * FROM table WHERE column = 5"

		#	"SELECT * FROM table WHERE column = ?"						args = 5; DROP TABLE table
		#	"SELECT * FROM table WHERE column = 5"

		#	"SELECT * FROM table WHERE column = ?; DROP TABLE table"		args = 5 
		#	"SELECT * FROM table WHERE column = 5; DROP TABLE table"

		normalized_string = ""
		prev_iter = 0
		iter = 0
		args_iter = 0
		
		while True:
			iter = string.find("?", iter)

			if (iter == -1):
				normalized_string += string[prev_iter:]
				break
			
			normalized_string += string[prev_iter:iter]
			arg = args[args_iter]
			args_iter += 1

			if isinstance(arg, str):
				normalized_string += await self.__shielding__(arg)
			elif isinstance(arg, int):
				normalized_string += str(arg)
			elif arg == None:
				normalized_string += "NULL"

			iter += 1
			if (iter >= len(string)):
				break
			prev_iter = iter

		return normalized_string


	async def __shielding__(self, string: "str") -> "str":
		shielded_string = ""
		
		shielded_string += "'"

		for symbol in string:
			if symbol == "\"" or symbol == "\'" or symbol == "\\":
				shielded_string += "\\" 
			shielded_string += symbol 

		shielded_string += "'"

		return shielded_string
	


	#	Other methods:
	def __increment_and_update_query_stat__(self):
		self.__query_stat_counter__ += 1
		self.query_per_sec = self.__query_stat_counter__ / (time() - self.__query_stat_start__)
		self.query_per_min = self.query_per_sec * 60
		pass


	async def __connections_checker__(self):
		while True:
			if (await self.checkConnections()):
				await asyncio.sleep(CHECK_CONNECTION_TIMEOUT)
			pass
		pass


	async def checkConnections(self):
		#	True - all good 
		#	False - have restarts 
		status = True
		for index, connection in enumerate(self.connections.copy()):
			if (connection["is_free"] and connection["last_executing"] < time() + WAIT_AFTER_QUERY_SECS):
				self.connections[index]["is_free"] = False
				try:
					connection["cursor"].execute(COMMAND_FOR_CHECK_CONNECTION)
					connection["cursor"].fetchall()
				except Exception as e:
					print(f"DB EXCEPTION: {e}\n\nSOCKET CLOSED!\nOne connection to database is broken!\nReconnect...")
					con = mysql.connect(host=self.__host__, port=self.__port__, 
										user=self.__user__, password=self.__password__, 
										database=self.__database__)
					curs = con.cursor()
					self.connections[index]["connection"].disconnect()
					self.connections[index]["connection"] = con
					self.connections[index]["cursor"] = curs
					status = False
					pass
				self.connections[index]["last_executing"] = time()
				self.connections[index]["is_free"] = True
				pass
			pass
		return status
	pass