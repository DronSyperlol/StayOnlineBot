from modules.UserBot import UserBot 
from modules.Database import DataBase
from modules.Proxy import Proxys
from modules.Structs import BotInfo
from random import randint
from time import time
import os
import asyncio


from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector


BOT_LIFETIME = 300
WAIT_FREE_SPACE = 10


class UserBots:
	def __init__(self, session_directory, DBAuthKey, api_id, api_hash, lower_threshold, upper_threshold, max_loaded_sessions = 200, proxys: Proxys = None):
		self.loaded_sessions = {}
		self.session_directory = session_directory
		self.db = DataBase(DBAuthKey)
		self.proxys = proxys
		self.api_id = api_id
		self.api_hash = api_hash
		self.lower_threshold = lower_threshold
		self.upper_threshold = upper_threshold
		self.max_loaded_sessions = max_loaded_sessions
		self.sessions = self.getLocalSessions()
		self.safeLoadBotsBuffer = []
		self.processNewMessages = None 
		self.notifyAboutBrokenBot = None 
		self.nextNotify = 0
		self.action_queue = []
		asyncio.get_event_loop().run_until_complete(self.updateProxysPopularity())
		pass

	#	Configure object
	def initCallbacks(self, processNewMessages, notifyAboutBrokenBot, notifyForAdminsAboutBrokenProxy):
		self.processNewMessages = processNewMessages
		self.notifyAboutBrokenBot = notifyAboutBrokenBot
		self.notifyForAdminsAboutBrokenProxy = notifyForAdminsAboutBrokenProxy
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


	def canLoadCount(self):
		return self.max_loaded_sessions - len(self.loaded_sessions)
	


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
		proxy = None
		if (not self.proxys.is_empty()):
			proxy = self.proxys.getUnpopular()
		bot = UserBot(self.session_directory, session_name, proxy, self.api_id, self.api_hash)
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
		bot = self.getBot(bot_phone_id)
		final_name = f"{bot.phone}.session"
		tmp_name = f"tmp_{bot_phone_id}.session"
		self.killUBot(bot_phone_id)
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
		await self.db.newBot(	int(bot.phone), owner, 
								None if (not bot.proxy) else bot.proxy["hostname"], 
								self.generateNexLoginTime())
		await self.updateProxysPopularity()
		pass



	# starting bots:
	async def startUBot(self, bot_phone_id, owner, proxy = None):
		bot = UserBot(self.session_directory, str(bot_phone_id), proxy, self.api_id, self.api_hash, owner)
		if (bot_phone_id in self.loaded_sessions):
			raise Exception("Bot already started")
		self.loaded_sessions[bot_phone_id] = bot
		bot.start()
		await bot.logIn()
		return bot
	
	
	##################
	#	Возвращает запущеного бота, если тот был запущен
	async def getOrStartUBot(self, bot_phone_id, bot_info: BotInfo = None, start_anyway = False, process_broken_bots = False):
		if (bot_phone_id in self.loaded_sessions):
			return self.loaded_sessions[bot_phone_id]
		if (not start_anyway and self.canLoadCount() <= 0):
			raise StartedMaxBots()
		if (bot_info == None):
			bot_info = await self.db.getBotInfo(bot_phone_id)
			if (bot_info == None):
				return None
		bot = await self.startUBot(bot_phone_id, bot_info.owner, self.proxys.getByHostname(bot_info.proxy_hostname))
		if (process_broken_bots):
			if (not bot.is_active):
				await self.processBrokenBot(bot_info.owner, bot_phone_id)
				return None
		return bot
	

	#	Запускает пул ботов
	async def safeLoadBotsPool(self, bots_info: list[BotInfo]):
		loaded_sessions = []
		tasks = []
		for bot_info in bots_info.copy():
			if (bot_info.bot_phone_id in self.safeLoadBotsBuffer):
				bots_info.remove(bot_info)
			else:
				self.safeLoadBotsBuffer.append(bot_info.bot_phone_id)
				tasks.append({
					"bot_phone_id" : bot_info.bot_phone_id,
					"task" : asyncio.create_task(self.getOrStartUBot(bot_info.bot_phone_id, bot_info))
				})
			pass
		for task in tasks:
			try:
				bot = await task["task"]
				loaded_sessions.append(bot)
			except StartedMaxBots:
				continue
			except Exception as e:
				print(f"Unknown exception in \"safeLoadBotsPool\"\nDetails: {e}")
				pass
		for bot_info in bots_info:
			self.safeLoadBotsBuffer.remove(bot_info.bot_phone_id)
			pass
		return loaded_sessions


	#############
	#	Убивает бота:
	def killUBot(self, bot_phone_id):
		if (bot_phone_id in self.loaded_sessions):
			self.loaded_sessions[bot_phone_id].kill()
			del self.loaded_sessions[bot_phone_id]
			return True
		return False
	
	async def killOldUBots(self):	#	checker
		for key in self.loaded_sessions:
			if (self.loaded_sessions[key].dead_time < time()):
				self.killUBot(key)
				pass
			pass
		pass




	#	Work methods:
	# Do online:
	async def checkNextLogins(self):
		bots_for_start = await self.db.getNearestNextLoginBots()
		if (not bots_for_start):
			return
		loaded_bots = await self.safeLoadBotsPool(bots_for_start)
		tasks = []
		for bot in loaded_bots:
			if (not bot.is_active):
				tasks.append(self.processBrokenBot(bot.owner, int(bot.name)))
				continue
			tasks.append(asyncio.create_task(self.proccessNextLogin(bot, int(bot.phone))))
			pass
		for task in tasks:
			await task
			pass


	async def proccessNextLogin(self, bot: UserBot, bot_phone_id):		# TODO... Надо сократить это говно!!!
		do_online_task = asyncio.create_task(self.updateOnlineStatus(bot_phone_id, bot))
		update_messages_task = asyncio.create_task(self.updateUnreadMessages(bot_phone_id, bot))
		await do_online_task
		await update_messages_task
		await self.db.updateNextLogin(bot_phone_id, self.generateNexLoginTime())
		self.killUBot(bot_phone_id)
		pass


	def generateNexLoginTime(self):
		return int(time() + randint(self.lower_threshold, self.upper_threshold))


	


	async def updateUnreadMessages(self, bot_phone_id, bot: UserBot = None, update_after = 0):
		if (not bot):
			bot = await self.getOrStartUBot(bot_phone_id, start_anyway=True, process_broken_bots=True)
			if (bot == None):
				return False
		bot.deadAfter(update_after + 60)
		await asyncio.sleep(update_after)
		result = await bot.getUnreadMessagesInfo()
		for sender_object in result:
			await self.processNewMessages(sender_object, bot_phone_id, bot.id, bot.owner)
			return True
		return False
	
	async def readUnreadMessages(self, bot_phone_id, bot: UserBot = None, update_after = 0):
		if (not bot):
			bot = await self.getOrStartUBot(bot_phone_id, start_anyway=True, process_broken_bots=True)
			if (bot == None):
				return False
		bot.deadAfter(update_after + 60)
		await asyncio.sleep(update_after)
		result = await bot.readMessages()
		return result

	async def updateOnlineStatus(self, bot_phone_id, bot: UserBot = None, update_after = 0):
		if (not bot):
			bot = await self.getOrStartUBot(bot_phone_id, start_anyway=True, process_broken_bots=True)
			if (bot == None):
				return False
		bot.deadAfter(update_after + 60)
		await asyncio.sleep(update_after)
		if (await bot.updateOnlineStatus(True)):
			return True
		return False


	async def processBrokenBot(self, owner, bot_phone_id):
		await self.notifyAboutBrokenBot(owner, bot_phone_id)
		await self.delBrokenBot(bot_phone_id)
		pass


	async def delBrokenBot(self, bot_phone_id):
		self.killUBot(bot_phone_id)
		await self.db.delBot(bot_phone_id)
		for _ in range(3):
			try:
				if (os.path.exists(f"{self.session_directory}{bot_phone_id}.session")):
					os.remove(f"{self.session_directory}{bot_phone_id}.session")
				if (os.path.exists(f"{self.session_directory}{bot_phone_id}.session-journal")):
					os.remove(f"{self.session_directory}{bot_phone_id}.session-journal")
				pass
			except:
				pass
		pass


	# Respones for sender:
	async def sendResponse(self, bot_phone_id, sender_id, sender_msg_id, text, str_sender_id, is_reply = False):
		if (not is_reply):
			sender_msg_id = None	# Если это не ответ, то id сообщения нахуй не нужен
		attemps = 120
		for _ in range(attemps):
			try:
				bot = await self.getOrStartUBot(bot_phone_id)
				break
			except StartedMaxBots:
				await asyncio.sleep(WAIT_FREE_SPACE)
			except Exception as e:
				print(f"Unknown exception in \"sendResponse\"\nDetails: {e}")
				return False
		else:
			print(f"Method \"sendResponse\" can't start bot {bot_phone_id}. Free spaces: {self.canLoadCount()}")
			return False
		await bot.sendMessage(sender_id, text, str_sender_id, sender_msg_id)
		return True




	##########
	#	Proxy:
	#
	async def updateProxysPopularity(self):
		proxy_stat = await self.db.getProxyStat()
		self.proxys.setPopularityAll(0)
		for proxy in proxy_stat:
			self.proxys.setPopularity(proxy.hostname, proxy.bots_quantity)
			pass
		pass


	async def checkProxys(self, 
		  proxys_for_check: list = None, 
		  disable_second_check = False, 
		  notify_if_broken = False):
		checking_url_list = [
			"https://time100.ru/api",
			"https://postman-echo.com/get?text=helloworld"
		]
		second_check = []

		if (not proxys_for_check):
			proxys_for_check = self.proxys.list()

		for server in proxys_for_check:
			proxy_url = server.proxy_info["scheme"] + "://" + server.proxy_info["username"] + ":" + server.proxy_info["password"] + "@" + server.proxy_info["hostname"] + ":" + str(server.proxy_info["port"])
			proxy_status = False
			tasks = []
			for url in checking_url_list:
				tasks.append([
					asyncio.create_task(
						self.getQuery(url, proxy_url)
					),
					server.proxy_info["hostname"]
				])
				pass
			
			for task in tasks:
				try:
					time_start = time()
					async with asyncio.timeout(50):
						response = await task[0]
					if (response.status == 200):
						proxy_status = True
					print(f"Check proxys. From {task[1]} GET to {response.url}, ms: {int((time() - time_start) * 1000)}, code: {response.status}")
				except:
					pass
				pass
			if (not proxy_status):
				second_check.append(server)
			if (proxy_status != server.is_active):
				self.proxys.setActivity(server.proxy_info["hostname"], proxy_status)
			pass
		del proxys_for_check
		del checking_url_list
		if (notify_if_broken and time() > self.nextNotify):
			self.nextNotify = time() + 3600 * 5
			broken_hostnames_list = [server.proxy_info["hostname"] for server in second_check]
			broken_proxy_txt_list = ""
			for hostname in broken_hostnames_list:
				broken_proxy_txt_list += f"{hostname}\n"
			print(f"Notify about broken proxys. Hostnames:\n{broken_proxy_txt_list}")
			await self.notifyForAdminsAboutBrokenProxy(broken_hostnames_list)
		if (second_check and not disable_second_check):
			await asyncio.sleep(120)
			await self.checkProxys(second_check, True, True)
			pass
		pass


	async def getQuery(self, url, proxy_url):
		connector = ProxyConnector.from_url(proxy_url)
		async with ClientSession(connector=connector) as session:
			async with await session.get(url) as response:
				return response
			



class InvalidData(Exception):
	pass

class StartedMaxBots(Exception):
	def __init__(self) -> None:
		super().__init__("Сan't run bots more than the specified limit")
	pass