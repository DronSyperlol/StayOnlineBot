#	+-------
#	|
#	+-------



from pyrogram import Client 
from pyrogram import errors
from pyrogram.types.user_and_chats import User 
from pyrogram.raw.functions.account.update_status import UpdateStatus 
import multiprocessing
import json
import asyncio
from time import time



#	Consts:
WAITING_RESPONSE_TIMEOUT = 300
WAITING_CONNECT_TIMEOUT = 120
UBOT_LIFE_TIME = 120

FATAL_ERROR = -1

SIGNIN_NONE = 0
SIGNIN_SUCCESS = 1
SIGNIN_WAIT_PHONE = 10
SIGNIN_WAIT_CODE = 11
SIGNIN_WAIT_PASSWORD = 12



#	Class UserBot
#	Оболочка для библиотеки Pyrogram
#	Осуществляет:
#		1.	Авторизацию аккаунта
#		2.	Появление в сети
#		3.	Чтение сообщений


'''
	Общение между процессами бота и родителя:
	
	Вызов (отправляется родителем):
		call: {
			* call 	- Имя функции для вызова
			* id	- Уникальный идентификатор вызова
			args	- (Не обязательно) Список аргументы вызова
		}

	Ответ (Отправляется процессом бота):
		response: {
			* call	- Возвращает имя функции 
			* id		- Возвращает id исполненого вызова
			* response	- Ответ от функции
			self	- (Не обязательно) Возвращает поля обеъекта для перезаписи у родителя
		}

		response: {
			* call: "notifyed complete task"	- уведомление о завершении задачи, которая ставится вызовом __set_task__.
			* task_id
			* result
		}
'''

class UserBot(multiprocessing.Process):
	def __init__(self, session_directory, session_name, proxy = None, app_id = None, app_hash = None, owner = None):
		multiprocessing.Process.__init__(self=self, name=session_name)
		self.app_id = app_id
		self.app_hash = app_hash 
		self.folder = session_directory
		self.status = 0
		#	0 - no info
		#	1 - is logined
		#	10 - waiting phone
		#	11 - waiting code
		#	12 - waiting password
		self.is_active = False
		self.phone = None
		self.id = None
		self.first_name = None
		self.owner = owner
		self.dead_time = int(time()) + UBOT_LIFE_TIME
		#	/\ /\ /\ Cached info about account
		self.proxy = proxy
		self.task_id = 0
		self.q_call = multiprocessing.Queue(5)
		self.q_resp = multiprocessing.Queue(5)
		self.executing_tasks = []
		self.response_storage = {}
		self.notify_storage = {}
		self.__authorization_data__ = {}
		pass

	def __del__(self):
		self.q_call.close()
		self.q_resp.close()
		pass


	def deadAfter(self, secs):
		self.dead_time = time() + secs 
		pass


	#
	#	Available methods:
	#

	# Authorization methods:
	async def connect(self):
		return await self.call_func("__connect__")
	

	async def askCode(self, phone: str):
		return await self.call_func("__askCode__", phone)


	async def setCode(self, phone, phone_code_hash, code):
		return await self.call_func("__setCode__", [phone, phone_code_hash, code])


	async def setPassword(self, password):
		return await self.call_func("__setPassword__", password)


	async def doLogin(self, data):
		if (not data and self.status > 0):
			return "Argument is empty"
		
		match (self.status):
			case 0:		#	Начало авторизации
				connect_result = await self.connect()
				if (connect_result):
					return "Already authorized"
				elif (connect_result == None):
					raise Exception("Can't connect to server")
				
				self.status = SIGNIN_WAIT_PHONE
				if (data):
					return await self.doLogin(data)
				return "Connected"

			case 10: #	SIGNIN_WAIT_PHONE
				phone_code_hash = await self.askCode(data)

				self.__authorization_data__["phone"] = data
				self.__authorization_data__["phone_code_hash"] = phone_code_hash
				
				self.status = SIGNIN_WAIT_CODE #	Ожидание кода
				return "Waiting code"
			
			case 11: #	SIGNIN_WAIT_CODE
				#	Status codes:
				#		-1	- fatal error
				#		0	- bad request. Try again
				#		1	- bot authorized
				#		10 	- need password
				result = await self.setCode(self.__authorization_data__["phone"], self.__authorization_data__["phone_code_hash"], data)
				match (result["code"]):
					case 0: #	SIGNIN_NONE
						return result["comment"]
					case 1: #	SIGNIN_SUCCESS
						self.status = SIGNIN_SUCCESS
						return "Success"
					case 12: #	SIGNIN_WAIT_PASSWORD
						self.status = SIGNIN_WAIT_PASSWORD
						return "Waiting password"
					case -1: #	FATAL_ERROR
						raise Exception(result["comment"])

			case 12: #	SIGNIN_WAIT_PASSWORD
				#	Status codes:
				#		-1	- fatal error
				#		0	- bad request. Try again
				#		1	- bot authorized
				result = await self.setPassword(data)
				match (result["code"]):
					case 0:	#	FATAL_ERROR
						return result["comment"]
					case 1: #	SIGNIN_SUCCESS
						self.status = SIGNIN_SUCCESS
						return "Success"
					case -1: #	FATAL_ERROR
						raise Exception(result["comment"])
				pass
		pass


	async def logIn(self):
		return await self.call_func("__logIn__")


	# work:
	async def updateOnlineStatus(self, is_online = True):
		return await self.call_func("__update_online_status__", is_online)


	async def getUnreadMessagesInfo(self):
		return await self.call_func("__get_unread_messages_info__")


	async def readMessages(self):
		return await self.call_func("__read_messages__")
	
	
	async def sendMessage(self, chat_id, text, str_chat_id, reply_to_message_id = None):
		return await self.call_func("__send_message__", [chat_id, text, str_chat_id, reply_to_message_id])




	# other methods:
	async def check(self):
		return await self.call_func("__check__")



	#
	#	Sending and receiving messages:	
	#
	async def call_func(self, call_name, args: list = None):
		call = {}
		call["call"] = call_name
		call["id"] = self.__get_call_id__()
		if (args):
			if (not isinstance(args, list)):
				args = [args]
			call["args"] = args
		self.q_call.put(json.dumps(call))
		response = await self.wait_response(call["id"])
		if (response == None):
			raise Exception(f"response is a null\nTS: {time()}\nCall obj: {str(call)}\nBot: {self.name} {'Flag: is_active' if self.is_active else ''}")
		if ("self" in response):
			self.is_active = response["self"]["is_active"]
			self.phone = response["self"]["phone"]
			self.id = response["self"]["id"]
			self.first_name = response["self"]["first_name"]
		return response["response"]

	async def wait_response(self, id, attemps = WAITING_RESPONSE_TIMEOUT // 3):
		while attemps > 0:
			try:
				if (id in self.response_storage):
					ret = self.response_storage[id]
					del self.response_storage[id]
					return ret
				response = json.loads(self.q_resp.get(False))
				if (response["call"] == "notifyed complete task"):
					self.notify_storage[response["task_id"]] = response["result"]	
					if (id == -1):
						return None
				else:
					self.response_storage[response["id"]] = response
			except:
				await asyncio.sleep(3)
				attemps -= 1
		print("wait response timeout ended")
		return None

	def __get_call_id__(self):
		self.task_id += 1
		return self.task_id



	#
	#	Call handler: (Executing in other process)
	#
	def run(self):
		if (self.app_hash and self.app_id):
			self.app = Client(self.name, self.app_id, self.app_hash, proxy=self.proxy, workdir=self.folder)
		else:
			self.app = Client(self.name, proxy=self.proxy, workdir=self.folder)
		print("Process PID: ", multiprocessing.current_process().pid, " Session: ", multiprocessing.current_process().name)

		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		loop.run_until_complete(self.__async_handler__())
			

	async def __async_handler__(self):
		while True:
			
			call = None
			while (not call):
				try:
					call = self.q_call.get(False, 5)
				except:
					await asyncio.sleep(5)
			#
			#	call - JSON строка
			#	Аргументы: 
			#		call - имя метода который нужно вызвать
			#		args - список аргументов которые нужно передать методу. Указываются по порядку. Необязательно
			#	
			#
			#	response - JSON строка
			#	Аргументы: 
			#		call - имя функции вызванной метода
			#		response - возвращенное значение метода в строке.
			#		self - объект типа ключ=значение обозначающее переменную класса и её значение ({phone: 88005553535})
			#	

			print("call: ", call)
			call = json.loads(call)	#	Parse in JSON
			response = {
				"call": call["call"],
				"id": call["id"]
			}
			match(call["call"]):

				case "__connect__":
					response["response"] = None
					try:
						if (await self.app.connect()):
							response["response"] = True
						else:
							response["response"] = False
					except Exception as e:
						print("Connect exception: ", e)
						pass
					pass

				case "__askCode__":
					response["response"] = await self.__askCode__(call["args"][0])
					pass
					
				case "__setCode__":
					response["response"] = await self.__setCode__(call["args"][0], call["args"][1], call["args"][2])
					if (response["response"]["code"] == SIGNIN_SUCCESS):
						response["self"] = {
							"is_active": self.is_active,
							"phone": self.phone,
							"id": self.id,
							"first_name": self.first_name
						}
						pass
					pass
					
				case "__setPassword__":
					response["response"] = await self.__setPassword__(call["args"][0])
					if (response["response"]["code"] == SIGNIN_SUCCESS):
						response["self"] = {
							"is_active": self.is_active,
							"phone": self.phone,
							"id": self.id,
							"first_name": self.first_name
						}
						pass
					pass
				
				case "__logIn__":
					response["response"] = await self.__logIn__()
					response["self"] = {
						"is_active": self.is_active,
						"phone": self.phone,
						"id": self.id,
						"first_name": self.first_name
					}
					pass

				case "__check__":
					response["response"] = await self.__check__()
					response["response"] = {
						"is_active": self.is_active,
						"phone": self.phone,
						"id": self.id,
						"first_name": self.first_name
					}
					pass

				case "__update_online_status__":
					response["response"] = await self.__update_online_status__(call["args"][0])
					pass

				case "__get_unread_messages_info__":
					response["response"] = await self.__get_unread_messages_info__()
					pass
				
				case "__read_messages__":
					response["response"] = await self.__read_messages__()

				case "__send_message__":
					response["response"] = await self.__send_message__(call["args"][0], call["args"][1], call["args"][2], call["args"][3])
					response["response"] = str(response["response"])
					pass
			
			print("response: ", response)
			self.q_resp.put(json.dumps(response))
		pass 


	#
	#	Telegram methods:
	#

	# authorization
	async def __askCode__(self, phone: str):
		try:
			result = await self.app.send_code(phone)
		except:
			return None
		return result.phone_code_hash

	async def __setCode__(self, phone, phone_code_hash, code):
		#	Status codes:
		#		-1	- fatal error
		#		0	- bad request. Try again
		#		1	- bot authorized
		#		12 	- need password
		response = {
			"code": SIGNIN_NONE,
			"comment":""
		}
		try:
			result = await self.app.sign_in(phone, phone_code_hash, code)
			if (isinstance(result, User)):
				self.is_active = True
				self.phone = result.phone_number
				self.id = result.id
				self.first_name = result.first_name
				response["code"] = SIGNIN_SUCCESS
		except errors.BadRequest as BadRequestDetails:
			response["code"] = SIGNIN_NONE
			response["comment"] = f"Bad request\nDetails: {BadRequestDetails}"
			pass
		except errors.SessionPasswordNeeded:
			response["code"] = SIGNIN_WAIT_PASSWORD
			response["comment"] = f"Need password"
			pass
		except Exception as e:
			response["code"] = FATAL_ERROR
			response["comment"] = f"Unexpected exception {e}"
		return response

	async def __setPassword__(self, password):
		#	Status codes:
		#		-1	- fatal error
		#		0	- bad request. Try again
		#		1	- bot authorized
		response = {
			"code": SIGNIN_NONE,
			"comment":""
		}
		try:
			result = await self.app.check_password(password)
			if (isinstance(result, User)):
				self.is_active = True
				self.phone = result.phone_number
				self.id = result.id
				self.first_name = result.first_name
				response["code"] = SIGNIN_SUCCESS
		except errors.BadRequest as BadRequestDetails:
			response["code"] = SIGNIN_NONE
			response["comment"] = f"Bad request\nDetails: {BadRequestDetails}"
		except Exception as e:
			response["code"] = FATAL_ERROR
		return response
	

	# login exists session
	async def __logIn__(self):
		try:
			async with asyncio.timeout(WAITING_CONNECT_TIMEOUT):
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
			#self.phone = self.id = self.first_name = None
			return False

		self.is_active = True
		self.phone = user_info.phone_number
		self.id = user_info.id
		self.first_name = user_info.first_name
		return True
	

	#	Low level API:
	async def __update_online_status__(self, is_online = True):
		try:
			func = UpdateStatus(offline=(not is_online))
			return await self.app.invoke(func)
		except:
			return None
		pass


	async def __get_unread_messages_info__(self):
		#	return list of sender objects
		#	sender object: {
		#		from: {
		#			name 		- sender first name
		#			username 	- sender username
		#			id 			- sender id
		# 		},
		#		messages: [			- dict of unread messages from this sender
		#			{	#	if text
		#				type: 'TEXT',
		#				id:	- message.id,
		#				text: 		- message.text,
		# 			},
		#			{	#	if media (photo)
		#				type: 'PHOTO',
		#				id:	- message.id,
		# 				file_name: 	- downloaded file,
		# 				caption:	- file caption
		# 			}
		# 		]
		# 	}
		ret = []
		try:
			result = self.app.get_dialogs()
		except:
			return None
		try:
			async for dialog in result:
				if (dialog.unread_messages_count <= 0 or 
						dialog.chat.type.name != "PRIVATE"):
					continue
				message_object = {
					"from": {},
					"messages": []
				}
				message_object["from"]["first_name"] = dialog.chat.first_name
				message_object["from"]["id"] = dialog.chat.id
				message_object["from"]["username"] = dialog.chat.username
				try:
					chat_history = self.app.get_chat_history(dialog.chat.id, dialog.unread_messages_count)
					async for message in chat_history:
						if (message.from_user.id == self.id):
							continue
						if (message.text):
							message_object["messages"].append({
								"type":		"TEXT",
								"id":		message.id,
								"text":		message.text
							})
						if (message.media and message.media.name == "PHOTO"):
							await self.app.download_media(message, f"./downloads/photo_{message.from_user.id}_{message.id}.jpg")
							message_object["messages"].append({
								"type":			"PHOTO",
								"id":			message.id,
								"file_name":	f"./downloads/photo_{message.from_user.id}_{message.id}.jpg",
								"caption": 		message.caption
							})
						pass
					pass
				except:
					pass
				pass
				ret.append(message_object)
			pass
		except:
			pass
		return ret
	

	async def __read_messages__(self):
		try:
			result = self.app.get_dialogs()
		except:
			return False

		try:
			async for dialog in result:
				if (dialog.unread_messages_count <= 0):
					continue
				await self.app.read_chat_history(dialog.chat.id)
		except:
			pass
		return True
	

	async def __send_message__(self, chat_id, text, str_chat_id = "", reply_to_message_id = None):
		try:
			await self.app.read_chat_history(chat_id)
			result = await self.app.send_message(chat_id, text, reply_to_message_id=reply_to_message_id)
			return result
		except:
			if (not str_chat_id):
				return None
			pass
		try:
			await self.app.read_chat_history(str_chat_id)
			result = await self.app.send_message(str_chat_id, text, reply_to_message_id=reply_to_message_id)
			return result
		except:
			return None
		pass