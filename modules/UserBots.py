from modules.UserBot import UserBot 
from modules.Database import DataBase
from random import randint
from time import time
import os



class UserBots:
	def __init__(self, session_directory, DBAuthKey, api_id, api_hash, lower_threshold, upper_threshold):
		self.loaded_sessions = {}
		self.session_directory = session_directory
		self.db = DataBase(DBAuthKey)
		self.api_id = api_id
		self.api_hash = api_hash
		self.lower_threshold = lower_threshold
		self.upper_threshold = upper_threshold
		self.sessions = self.getLocalSessions()


	def getLocalSessions(self) -> list:
		sessions = []
		sessions = os.listdir(self.session_directory)
		for index, session in enumerate(sessions.copy()):
			if ("-journal" in session or "tmp" in session):
				sessions.remove(session)
				continue
		for index, session in enumerate(sessions.copy()):
			sessions[index] = session.replace(".session", "")
		return sessions


	def getBot(self, bot_phone_id):
		if (bot_phone_id in self.loaded_sessions):
			return self.loaded_sessions[bot_phone_id]
		return None


	# authorization
	async def newBot(self, phone: str):
		bot_phone_id = int(phone.replace('+', ''))
		session_name = f"tmp_{bot_phone_id}"
		bot = UserBot(self.session_directory, session_name, None, self.api_id, self.api_hash)
		self.loaded_sessions[bot_phone_id] = bot
		bot.start()
		return await bot.doLogin(phone)

	async def setCodeForBot(self, bot_phone_id: int, code):
		bot = self.getBot(bot_phone_id)
		if (not bot):
			raise Exception(f"Can't get bot by bot_phone_id: {bot_phone_id}")
		return await bot.doLogin(code)
	
	async def setPasswordForBot(self, bot_phone_id: int, password: str):
		bot = self.getBot(bot_phone_id)
		if (not bot):
			raise Exception(f"Can't get bot by bot_phone_id: {bot_phone_id}")
		return await bot.doLogin(password)


	# initialize
	async def initUBot(self, bot_phone_id, owner):
		final_name = f"{bot_phone_id}.session"
		tmp_name = f"tmp_{bot_phone_id}.session"

		bot = self.getBot(bot_phone_id)
		bot.kill()
		
		if (os.path.exists(self.session_directory + tmp_name)):
			if (os.path.exists(self.session_directory + final_name)):
				os.remove(self.session_directory + final_name)
			os.rename(self.session_directory + tmp_name, self.session_directory + final_name)
			os.remove(self.session_directory + tmp_name + "-journal")
			pass
		await self.db.newBot(bot_phone_id, owner, self.generateNexLoginTime())
		pass



	# starting bots:
	async def startUBot(self):
		pass
		

	#	Do online:
	async def checkNextLogins(self):

		pass

	def generateNexLoginTime(self):
		return int(time() + randint(self.lower_threshold, self.upper_threshold))
	pass
