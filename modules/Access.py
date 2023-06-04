#	+-------
#	|	Developer:	Syperlol aka Dron aka DronSyperlol
#	|	Contacts:	t.me/Syperlol github.com/DronSyperlol
#	|	
#	+-------


#   Access codes:
ROOT = 9    #   9x -> 90 - 99
AMDIN = 8   #   8x -> 80 - 89
USER = 1    #   1x -> 10 - 19

class Access: 
	def __init__(self):
		self.white_list = []
		#   White list:
		#   [{
		#       "user_id":  -   Telegram id
		#       "rank":     -   He's rank (privilegies)
		#   }]

		self.last_error = []
		#   Last error:
		#   [
		#       *code*,        -   Http error codes
		#       *description*   -   What's problem
		#   ]
		pass



	#   Giving access
	def giveAccess(self, user_id, rank):
		if (self.__exists__(user_id)):
			self.__set_last_error__(58, "Access already given")
			return False
		self.white_list.append(
			{
				"user_id" : user_id,
				"rank" : rank
			}
		)
		return True
	
	def dismiss(self, user_id):
		user = self.__find__(user_id)
		if (not user):
			return False
		self.white_list.remove(user)
		return True

	def updateRank(self, user_id, new_rank = 0):
		user = self.__find__(user_id)
		if (user):
			self.white_list[self.white_list.index(user)]["rank"] = new_rank
			return True
		return False



	#   Checkers:
	def check(self, user_id):
		return self.__exists__(user_id)

	def needUpdate(self, user_id):
		rank = self.getRank(user_id)
		status = rank - ((rank // 10) * 10)
		if (status != 9):
			return True
		return False

	def checkAccessLevel(self, user_id, level = 1):
		#   Level:
		#   1 - Just users, admins and root
		#   2 - Admins and root
		#   3 - Root only
		user = self.__find__(user_id)
		if (not user):
			return False
		match (user["rank"] // 10):
			case 9:
				if (level <= 3):
					return True

			case 8:
				if (level <= 2):
					return True

			case 1:
				if (level <= 1):
					return True

			case _:
				pass
		return False



	#	Giving info:
	def list(self):
		ret = []
		for user in self.white_list:
			ret.append({user["user_id"] : user["rank"]})
			pass
		return ret
	
	def getRank(self, user_id):
		user = self.__find__(user_id)
		if (user):
			return user["rank"]
		return 0



	#	Total actions:
	def initAll(self):
		for index, value in enumerate(self.white_list):
			rank = (value["rank"] // 10) * 10
			self.white_list[index]["rank"] = rank + 8
			pass
		pass



	#   Errors:
	def getLastError(self):
		return self.last_error
		
		
	def __set_last_error__(self, code, description = ""):
		self.last_error = [code, description]
		pass
		


	#   Work with white list:
	def __find__(self, user_id):
		for user in self.white_list:
			if (user["user_id"] == user_id):
				return user
		return None

		
	def __exists__(self, user_id):
		for user in self.white_list:
			if (user["user_id"] == user_id):
				return True
		return False

	pass