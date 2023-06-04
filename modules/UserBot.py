#	+-------
#	|
#	+-------



from pyrogram import Client 
from pyrogram import errors
import multiprocessing
import json
import asyncio
from time import time



#	Consts:
WAITING_RESPONSE_TIMEOUT = 120




#	Class UserBot
#	Оболочка для библиотеки Pyrogram
#	Осуществляет:
#		1.	Авторизацию аккаунта
#		2.	Появление в сети
#		3.	Чтение сообщений

class UserBot(multiprocessing.Process):
	def __init__(self, session_directory, session_name, proxy = None, app_id = None, app_hash = None):
		multiprocessing.Process.__init__(self=self, name=session_name)
		self.app_id = app_id
		self.app_hash = app_hash 
		self.folder = session_directory
		self.status = 0
		self.phone = None
		self.id = None
		self.first_name = None
		self.started_at = int(time())
		self.proxy = proxy
		self.task = multiprocessing.Queue(5)
		self.response = multiprocessing.Queue(5)
		self.executing_tasks = []
		self.response_storage = {}
		self.notify_storage = {}
		self.__authorization_data__ = {}
		pass

	def __del__(self):
		self.task.close()
		self.response.close()
		pass

	

	#
	#	Available methods:
	#
	#async def askCode(self):
	#	if (self.status >= 1):
	#		return False

	#	task = {}
	#	task["task"] = "__askCode__"

	#	self.task.put(json.dumps(task))
		
	#	response = await self.wait_response(task["task"])
	#	print("response: ", response)
		
	#	if (response == None):
	#		return False
		
	#	self.is_active = response["self"]["is_active"]
	#	self.phone = response["self"]["phone"]
	#	self.id = response["self"]["id"]
	#	self.first_name = response["self"]["first_name"]
			
	#	return response["response"]


	#async def setCode(self):
	#	pass


	#async def setPassword(self):
	#	pass
	async def connect(self):
		task = {"task": "__connect__"}
		self.task.put(json.dumps(task))
		response = await self.wait_response(task["task"])
		return response["response"]


	async def doLogin(self, data):
		match (self.status):
			case 0:		#	Начало авторизации
				await self.connect()

				task = {}
				task["task"] = "__askCode__"
				task["args"] = [data]

				self.task.put(json.dumps(task))
				
				response = await self.wait_response(task["task"])
				print("response: ", response)
				
				if (response == None):
					return "Error sending code"

				self.__authorization_data__["phone"] = data
				self.__authorization_data__["code"] = {
					"phone_code_hash": response["response"],
				}
				
				self.status = 2 #	Ожидание кода
				return "Waiting code"
			
			case 2:		#	Попытка входа по коду
				#task = {}
				#task["task"] = "__askCode__"

				#self.task.put(json.dumps(task))
				
				#response = await self.wait_response(task["task"])
				#print("response: ", response)
				
				#if (response == None):
				#	return "Error sending code"

				#self.__authorization_data__["phone"] = data
				#self.__authorization_data__["code"] = {
				#	"type": response["type"],
				#	"phone_code_hash": response["phone_code_hash"],
				#	"next_type": response["next_type"]
				#}
				
				#self.status = 3 #	Ожидание пароля
				return "Waiting code"
		pass



	async def logIn(self):
		task = {}
		task["task"] = "__logIn__"

		self.task.put(json.dumps(task))
		
		response = await self.wait_response(task["task"])
		print("response: ", response)
		
		if (response == None):
			return False
		
		self.is_active = response["self"]["is_active"]
		self.phone = response["self"]["phone"]
		self.id = response["self"]["id"]
		self.first_name = response["self"]["first_name"]
			
		return response["response"]



	async def check(self):
		task = {}
		task["task"] = "__check__"

		self.task.put(json.dumps(task))
		
		response = await self.wait_response(task["task"])
		print("response: ", response)
		
		if (response == None):
			return False
		
		self.is_active = response["self"]["is_active"]
		self.phone = response["self"]["phone"]
		self.id = response["self"]["id"]
		self.first_name = response["self"]["first_name"]
			
		return response["response"]



	async def protectSelf(self):
		task = {}
		task["task"] = "__protect_self__"

		self.task.put(json.dumps(task))
		
		response = await self.wait_response(task["task"])
		print("response: ", response)
		
		if (response == None):
			return False
			
		return response["response"]


		
	def readMessagesAsync(self):
		task = {}
		task["task"] = "__read_messages__"

		self.task.put(json.dumps(task))
		pass





	#
	#	Geting response:	
	#
	async def wait_response(self, task, attemps = WAITING_RESPONSE_TIMEOUT // 3):
		while attemps > 0:
			try:
				if (task in self.response_storage):
					ret = self.response_storage[task]
					del self.response_storage[task]
					return ret
				response = json.loads(self.response.get(False))
				if (response["task"] == "notifyed complete task"):
					self.notify_storage[response["task_id"]] = response["result"]	
					if (task == ""):
						return None
				else:
					self.response_storage[response["task"]] = response
			except:
				await asyncio.sleep(3)
				attemps -= 1
		print("wait response timeout ended")
		return None


	def wait_notify_complete(self, task_id, task_name, args, async_callback_func):
		async def __wait_notify_complete__(task_id, async_callback_func):
			while True:
				await self.wait_response("", 20)
				if (task_id in self.notify_storage):
					self.executing_tasks.remove(task_id)
					is_last = True
					if (self.executing_tasks):
						is_last = False
					await async_callback_func(task_id, task_name, self.id, args, self.notify_storage[task_id], is_last)
					del self.notify_storage[task_id]
					return
				await asyncio.sleep(60)
		asyncio.create_task(__wait_notify_complete__(task_id, async_callback_func))


	





	#
	#	Task handler: (Executing in other process)
	#
	def run(self):
		if (self.app_hash and self.app_id):
			self.app = Client(self.folder + self.name, self.app_id, self.app_hash, proxy=self.proxy)
		else:
			self.app = Client(self.folder + self.name, proxy=self.proxy)
		print("Process PID: ", multiprocessing.current_process().pid, " Session: ", multiprocessing.current_process().name)

		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		loop.run_until_complete(self.__async_handler__())
			

	async def __async_handler__(self):
		while True:
			
			task = None
			while (not task):
				try:
					task = self.task.get(False, 5)
				except:
					await asyncio.sleep(5)
			#
			#	task - JSON строка
			#	Аргументы: 
			#		task - имя метода который нужно вызвать
			#		args - список аргументов которые нужно передать методу. Указываются по порядку. Необязательно
			#	
			#
			#	response - JSON строка
			#	Аргументы: 
			#		task - имя функции вызванной метода
			#		response - возвращенное значение метода в строке.
			#		self - объект типа ключ=значение обозначающее переменную класса и её значение ({phone: 88005553535})
			#	

			print("task: ", task)
			task = json.loads(task)	#	Parse in JSON
			
			if task["task"] == "__connect__":
				response = {
					"task": task["task"],
					"response": False
				}
				try:
					await self.app.connect()
					response["response"] = True
				except:
					pass
				self.response.put(json.dumps(response))

			elif task["task"] == "__askCode__":
				response = {
					"task": task["task"],
					"response": await self.__askCode__(task["args"][0])
				}
				self.response.put(json.dumps(response))
				
			elif task["task"] == "__logIn__":
				response = {
					"task": task["task"],
					"response": await self.__logIn__(),
					"self": {
						"is_active": self.is_active,
						"phone": self.phone,
						"id": self.id,
						"first_name": self.first_name
					}
				}
				self.response.put(json.dumps(response))
				
			elif task["task"] == "__protect_self__":
				response = {
					"task": task["task"],
					"response": await self.__protect_self__()
				}
				self.response.put(json.dumps(response))
				
			elif task["task"] == "__check__":
				response = {
					"task": task["task"],
					"response": await self.__check__(),
					"self": {
						"is_active": self.is_active,
						"phone": self.phone,
						"id": self.id,
						"first_name": self.first_name
					}
				}
				self.response.put(json.dumps(response))

			elif task["task"] == "__read_messages__":
				self.__read_messages_async__()
				pass
		pass 



	#
	#	Tasks:
	#
	async def __set_task__(self, task_id, task, args, execute_time):
		if (task_id in self.executing_tasks):
			return False
		args = json.loads(args)
		self.executing_tasks.append(task_id)
		match(task):
			case "JOIN":
				sleep_time = execute_time - int(time())
				if (sleep_time < 0 and sleep_time >= -120):
					sleep_time = 0
				elif (sleep_time < -120):
					return False
				self.__delay_task__(sleep_time, lambda : self.__notify_when_complete__(task_id, lambda : self.__join__(args["target"])))
			
			case "LEAVE":
				sleep_time = execute_time - int(time())
				if (sleep_time < 0 and sleep_time >= -120):
					sleep_time = 0
				elif (sleep_time < -120):
					return False
				
				self.__delay_task__(sleep_time, lambda : self.__notify_when_complete__(task_id, lambda : self.__leave__(args["target"])))

			case "REPRT":
				sleep_time = execute_time - int(time())
				if (sleep_time < 0 and sleep_time >= -120):
					sleep_time = 0
				elif (sleep_time < -120):
					return False
				
				if ("message_ids" in args):
					self.__delay_task__(sleep_time, lambda : self.__notify_when_complete__(task_id, lambda : self.__report_post__(args["target"], args["message_ids"], args["reason"])))
				else:
					self.__delay_task__(sleep_time, lambda : self.__notify_when_complete__(task_id, lambda : self.__report_peer__(args["target"], args["reason"])))

		return True


	def __delay_task__(self, timeout_sec, async_callback_func):
		async def __set_interval__(timeout_sec, async_callback_func):
			await asyncio.sleep(timeout_sec)
			await async_callback_func()
		asyncio.create_task(__set_interval__(timeout_sec, async_callback_func))
		pass
	

	async def __notify_when_complete__(self, task_id, async_task_func):		#	Отправляет в response то, что вернула переданная callback функция
		response = {
			"task": "notifyed complete task",
			"task_id": task_id,
			"result": await async_task_func()
		}
		self.response.put(json.dumps(response))
		self.executing_tasks.remove(task_id)
		pass



	#
	#	Telegram methods:
	#
	async def __askCode__(self, phone: str):
		response = {}
		try:
			result = await self.app.send_code(phone)
		except:
			return None
		return result.phone_code_hash


	async def __setCode__(self, code):
		
		pass


	async def __logIn__(self):
		try:
			await self.app.connect()
			user_info = await self.app.get_me()
		except:
			return False

		self.is_active = True
		self.phone = user_info.phone_number
		self.id = user_info.id
		self.first_name = user_info.first_name
		return True


	async def __check__(self):
		try:
			user_info = await self.app.get_me()
		except:
			self.is_active = False
			self.phone = self.id = self.first_name = None
			return False

		self.is_active = True
		self.phone = user_info.phone_number
		self.id = user_info.id
		self.first_name = user_info.first_name
		return True
	

	#	Low level API:
	async def __protect_self__(self):
		ret_code = 0
		try:
			from hashlib import md5
			password = (md5(str(self.id).encode())).hexdigest()
			await self.app.enable_cloud_password(password)
			ret_code += 1
		except:		
			ret_code += 10
		try:
			from pyrogram.raw.functions.auth.reset_authorizations import ResetAuthorizations
			await self.app.invoke(ResetAuthorizations())
			ret_code += 2
		except:
			ret_code += 20
			from pyrogram.raw.functions.account.get_authorizations import GetAuthorizations
			result = await self.app.invoke(GetAuthorizations())
			ret_code *= 1000
			ret_code += len(result.authorizations)
			

		#	ret_code == 3	//	Sucess
		#	ret_code == 30	//	All bad
		#	ret_code == 21	//	ResetAuthorizations failure
		#	ret_code == 12 	//	Enable password failure
		
		return ret_code


	async def __report_post__(self, chat_id, message_ids = [], reason = "OTHER"):
		try:
			from pyrogram.raw.functions.messages.report import Report
			reason = self.__resolve_reason__(reason)
			peer = await self.app.resolve_peer(chat_id)
			report = Report(peer=peer, id=message_ids, reason=reason, message="")
			result = await self.app.invoke(report)
		except:
			result = False
		return result
	

	async def __report_peer__(self, chat_id, reason = "OTHER"):
		try:
			from pyrogram.raw.functions.account.report_peer import ReportPeer
			reason = self.__resolve_reason__(reason)
			peer = await self.app.resolve_peer(chat_id)
			report = ReportPeer(peer=peer, reason=reason, message="")
			result = await self.app.invoke(report)
		except:
			result = False
		return result

	
	def __resolve_reason__(self, reason: str):
		match(reason):
			case "PERSONALDETAILS":
				from pyrogram.raw.types.input_report_reason_personal_details import InputReportReasonPersonalDetails as reason_constructor
				return reason_constructor()
				
			case "ILLEGALDRUGS":
				from pyrogram.raw.types.input_report_reason_illegal_drugs import InputReportReasonIllegalDrugs as reason_constructor
				return reason_constructor()
				
			case "VIOLENCE":
				from pyrogram.raw.types.input_report_reason_violence import InputReportReasonViolence as reason_constructor
				return reason_constructor()
				
			case "CHILDABUSE":
				from pyrogram.raw.types.input_report_reason_child_abuse import InputReportReasonChildAbuse as reason_constructor
				return reason_constructor()
				
			case "PORNOGRAPHY":
				from pyrogram.raw.types.input_report_reason_pornography import InputReportReasonPornography as reason_constructor
				return reason_constructor()
				
			case "FAKE":
				from pyrogram.raw.types.input_report_reason_fake import InputReportReasonFake as reason_constructor
				return reason_constructor()
				
			case "COPYRIGHT":
				from pyrogram.raw.types.input_report_reason_copyright import InputReportReasonCopyright as reason_constructor
				return reason_constructor()
			
			case "SPAM":
				from pyrogram.raw.types.input_report_reason_spam import InputReportReasonSpam as reason_constructor
				return reason_constructor()
			
			case _:
				from pyrogram.raw.types.input_report_reason_other import InputReportReasonOther as reason_constructor
				return reason_constructor()
		pass



	async def __join__(self, target):	#	look Database description.txt
		response = None
		try:
			response = await self.app.join_chat(target)
		except errors.exceptions.bad_request_400.InviteRequestSent:
			return 1		#	Invite request sent
		except:
			pass

		if response and response.id:
			return 10		#	In channel
		else:
			return -1		#	Some error


	async def __leave__(self, target):
		try:
			await self.app.leave_chat(target, True)
		except:
			return -1
		return 1



	async def __get_chat__(self, link, get_full_info = False):
		try:
			result = await self.app.get_chat(link)
			id = result.id
			if (get_full_info):
				return [id, result.title, result.type.name]
		except:
			return 0
		return id
	

	async def __get_available_chats__(self):
		chat_ids = []
		try:
			result = self.app.get_dialogs()
		except:
			return chat_ids
		async for dialog in result:
			if (dialog.chat.type.value == "channel" or (dialog.chat.type.value == "group" and dialog.chat.permissions)):
				chat_ids.append(dialog.chat.id)
			pass
		return chat_ids
	


	def __read_messages_async__(self):
		async def __read_messages__(self):
			from random import randint
			try:
				result = self.app.get_dialogs()
			except:
				return False

			async for dialog in result:
				if (dialog.unread_messages_count <= 0):
					continue
				await self.app.read_chat_history(dialog.chat.id)
				await asyncio.sleep(randint(2, 20))
			return True
		asyncio.create_task(__read_messages__(self))
	pass