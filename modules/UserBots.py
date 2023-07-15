from modules.UserBot import UserBot 
from modules.Database import DataBase
from random import randint
from time import time
import os
import asyncio



BOT_LIFETIME = 300



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
		self.processNewMessages = None 
		self.action_queue = []

	#	Configure object
	def initCallbacks(self, processNewMessages):
		self.processNewMessages = processNewMessages
		pass

	#	Executing in self thread:
	def setAction(self, lambda_func_for_run):
		self.action_queue.append(lambda_func_for_run)
		pass
	
	def checkAndRunActions(self):
		while self.action_queue:
			action = self.action_queue.pop(0)
			asyncio.create_task(
				action()
			)
		pass


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


	def getBot(self, bot_phone_id) -> UserBot:
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
		for _ in range(3):
			try:
				if (os.path.exists(self.session_directory + tmp_name)):
					if (os.path.exists(self.session_directory + final_name)):
						os.remove(self.session_directory + final_name)
					os.rename(self.session_directory + tmp_name, self.session_directory + final_name)
					os.remove(self.session_directory + tmp_name + "-journal")
					pass
			except:
				await asyncio.sleep(1)
				pass
		await self.db.newBot(bot_phone_id, owner, self.generateNexLoginTime())
		pass



	# starting bots:
	async def startUBot(self, bot_phone_id, owner):
		bot = UserBot(self.session_directory, str(bot_phone_id), None, self.api_id, self.api_hash, owner)
		if (bot_phone_id in self.loaded_sessions):
			raise Exception("Bot already started")
		self.loaded_sessions[bot_phone_id] = bot
		bot.start()
		if (await bot.logIn()):
			return bot
		return None
	
	##################
	#	Возвращает запущеного бота, если тот был запущен
	async def getOrStartUBot(self, bot_phone_id):
		if (bot_phone_id in self.loaded_sessions and self.loaded_sessions[bot_phone_id].is_active):
			return self.loaded_sessions[bot_phone_id]
		return await self.startUBot(bot_phone_id, (await self.db.getBotOwner(bot_phone_id)))
		

	#	Work methods:
	# Do online:
	async def checkNextLogins(self):		# TODO... Надо сократить это говно!!!
		bots_for_start = await self.db.getNearestNextLoginBots()
		if (not bots_for_start):
			return
		start_tasks = []
		update_online_tasks = []
		get_messages_tasks = []
		for bot_info in bots_for_start:
			start_tasks.append(
				asyncio.create_task(
					self.startUBot(bot_info["bot_phone_id"], bot_info["owner"])
				)
			)
			pass
		for task in start_tasks:
			bot = await task
			if (bot):
				update_online_tasks.append({
					"bot": bot,
					"task": asyncio.create_task(
						bot.updateOnlineStatus()
					)
				})
				get_messages_tasks.append({
					"bot": bot,
					"task": asyncio.create_task(
						bot.getUnreadMessagesInfo()
					)
				})
				pass
			pass
		del start_tasks	#	БАЙТОЁБЛЮ АХАХАХХАХА

		for task in update_online_tasks:
			await task["task"]
			await self.db.updateNextLogin(int(task["bot"].phone), self.generateNexLoginTime())
			pass
		del update_online_tasks	#	БАЙТОЁБЛЮ АХАХАХХАХА

		for task in get_messages_tasks:
			result = await task["task"]
			for sender_object in result:
				await self.processNewMessages(sender_object, int(task["bot"].phone), task["bot"].id, task["bot"].owner)
			pass

		for task in get_messages_tasks:
			self.killUBot(int(task["bot"].phone))
			pass
		pass

	def generateNexLoginTime(self):
		return int(time() + randint(self.lower_threshold, self.upper_threshold))


	async def updateUnreadMessages(self, bot_phone_id):
		bot = self.getOrStartUBot(bot_phone_id)
		bot.deadAfter(120)
		await asyncio.sleep(60)
		result = await bot.getUnreadMessagesInfo()
		for sender_object in result:
			await self.processNewMessages(sender_object, int(bot.phone), bot.id, bot.owner)
		pass




	# Respones for sender:
	async def sendResponse(self, bot_phone_id, sender_id, sender_msg_id, text, str_sender_id, is_reply = False):
		if (not is_reply):
			sender_msg_id = None	# Если это не ответ, то id сообщения нахуй не нужен
		bot = await self.getOrStartUBot(bot_phone_id)
		await bot.sendMessage(sender_id, text, str_sender_id, sender_msg_id)
		pass


	#	kill bots:
	def killUBot(self, bot_phone_id):
		self.loaded_sessions[bot_phone_id].kill()
		del self.loaded_sessions[bot_phone_id]
		pass
	
	async def killOldUBots(self):
		for key, bot in self.loaded_sessions.items():
			if (bot.dead_time < time()):
				self.killUBot(key)
				pass
			pass
		pass
	pass
