#	+-------
#	|	Developer:	Syperlol aka Dron aka DronSyperlol
#	|	Contacts:	t.me/Syperlol github.com/DronSyperlol
#	|	
#	+-------



import mysql.connector as mysql
import asyncio

class Pool:
	def __init__(self, host, port, user, password, database, instances = 5):
		self.connections = []

		for i in range(instances):
			con = mysql.connect(host=host, port=port, user=user, password=password, database=database)
			curs = con.cursor()
			connection = {
				"connection": con,
				"cursor": curs,
				"is_free": True
			}
			self.connections.append(connection)
			pass
		
		
	async def execute(self, command, args = None):
		if args == None:
			return await self.__execute__(command)
		
		command = await self.__parse_command__(command, args)
		return await self.__execute__(command)
		

	async def __execute__(self, command):
		attemps = 20

		while attemps > 0:
			for index, connection in enumerate(self.connections):
				if (connection["is_free"]):
					self.connections[index]["is_free"] = False

					try:
						connection["cursor"].execute(command)
						result = connection["cursor"].fetchall()
						connection["connection"].commit()
					except:
						print("DATABASE EXCEPTION\n\n===============\n===============")
						return None

					self.connections[index]["is_free"] = True
					return result
			await asyncio.sleep(1)
			attemps -= 1
			pass
		return None


	async def __parse_command__(self, string: "str", args):
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
	

	pass