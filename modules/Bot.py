import telebot
from threading import Thread 
import asyncio
from modules.Access import Access
from modules.Database import DataBase
from modules.LastAction import LastAction
from modules.UserBots import UserBots
from modules.Proxy import Proxys
from time import sleep




class Bot:
	def __init__(self, api_key, DBAuthKey, admin_list: list, uBots: UserBots):
		self.bot = telebot.TeleBot(api_key)
		self.db = DataBase(DBAuthKey)
		self.la = LastAction()
		self.uBots = uBots
		
		self.access = Access()
		temp = asyncio.run(self.db.getWhiteList())
		for info in temp:
			rank = ((info.rank // 10) * 10) + 7
			self.access.giveAccess(info.user_id, rank)
		del temp
		for id in admin_list:
			if (not self.access.check(id)):
				self.access.giveAccess(id, 98)
			else:
				self.access.updateRank(id, 98)
			pass
		self.access.initAll()
		
		self.thread = Thread(target=self.__thread_bot__)
		self.text_handler_queue = []
		self.callback_handler_queue = []
		self.thread.start()
		pass






	def __thread_bot__(self):
		thread = Thread(target=self.__thread_handler__)
		thread.start()
		def callback_handler(data):
			self.callback_handler_queue.append(data)
			pass
		@self.bot.callback_query_handler(callback_handler)
		@self.bot.message_handler()
		def callback_func(message):
			self.text_handler_queue.append(message)
			pass
		self.bot.infinity_polling()
		pass

	def __thread_handler__(self):
		loop = asyncio.new_event_loop()
		async def __async_thread_handler__(self: Bot):
			while True:
				if (self.callback_handler_queue):
					task = asyncio.create_task(self.__callback_handler_async__(self.callback_handler_queue.pop(0)))
					await task
				if (self.text_handler_queue):
					task = asyncio.create_task(self.__async_text_handler__(self.text_handler_queue.pop(0)))
					await task
				sleep(0.1)
				pass
		loop.run_until_complete(__async_thread_handler__(self))
		pass

	async def __async_text_handler__(self, message): 
		la = self.la.get(message.from_user.id)
		if (la and 
      		await self.__last_action_handler__(message, la["code"], la["arg"])):
			return
		await self.__text_handler__(message)
			






	################
	#
	#	Last action handler:
	#
	################
	async def __last_action_handler__(self, message, code, arg):
		match (code):

			case 1:	
				if (message.text == "/cancel"):
					self.bot.send_message(message.chat.id, "Действие отменено")
					await self.__start_menu__(message.chat.id, None, self.access.checkAccessLevel(message.from_user.id, 2))
					return True
				arg["delete_messages"].append(message.id)

				result = self.bot.send_message(message.chat.id, "Подождите...")
				arg["delete_messages"].append(result.id)

				phone = ""
				if (message.text[0] != '+'):
					phone += '+'
				phone += message.text.replace(' ', '').replace('-', '')

				try:
					if (await self.uBots.newBot(phone) == "Waiting code"):
						result = self.bot.send_message(message.chat.id, "Отправьте мне код верификации чтобы я смог авторизовать аккаунт.\nОн уже был отправлен.")
						arg["delete_messages"].append(result.id)
						arg["bot_phone_id"] = int(phone.replace('+', ''))
						self.la.set(message.from_user.id, 2, arg)
						return True
				except:
					result = self.bot.send_message(message.chat.id, "Ошибка! Проверьте правильность введёных данных и повторите попытку\n\n/cancel для отмены")
					self.la.set(message.from_user.id, 1, arg)
					return True
				
				result = self.bot.send_message(message.chat.id, "Что-то пошло не так. Возможно аккаунт не существует.\nПроверьте правильность введённых данных и повторите попытку\n\n/cancel для отмены")
				arg["delete_messages"].append(result.id)
				self.la.set(message.from_user.id, code, arg)
				return True

			case 2:
				if (message.text == "/cancel"):
					self.bot.send_message(message.chat.id, "Действие отменено")
					await self.__start_menu__(message.chat.id, None, self.access.checkAccessLevel(message.from_user.id, 2))
					return True
				arg["delete_messages"].append(message.id)

				match (await self.uBots.setCodeForBot(arg["bot_phone_id"], message.text)):
					case "Waiting password":
						result = self.bot.send_message(message.chat.id, "Отправьте мне пароль от аккаунта чтобы я смог авторизовать аккаунт.\nОн уже был отправлен.")
						arg["delete_messages"].append(result.id)
						self.la.set(message.from_user.id, 3, arg)
						return True
				
					case "Success":
						result = self.bot.send_message(message.chat.id, f"Аккаунт +{arg['bot_phone_id']} успешно авторизован!")
						arg["delete_messages"].append(result.id)
						await self.uBots.initUBot(arg["bot_phone_id"], message.from_user.id)
						return True

					case _:
						result = self.bot.send_message(message.chat.id, f"Не удалось авторизовать аккаунт! Повторите попытку.\n/cancel для отмены")
						arg["delete_messages"].append(result.id)
						self.la.set(message.from_user.id, code, arg)
						return True
				pass

			case 3:
				if (message.text == "/cancel"):
					self.bot.send_message(message.chat.id, "Действие отменено")
					await self.__start_menu__(message.chat.id, None, self.access.checkAccessLevel(message.from_user.id, 2))
					return True
				arg["delete_messages"].append(message.id)

				match (await self.uBots.setPasswordForBot(arg["bot_phone_id"], message.text)):
					case "Success":
						result = self.bot.send_message(message.chat.id, f"Аккаунт +{arg['bot_phone_id']} успешно авторизован!")
						arg["delete_messages"].append(result.id)
						await self.uBots.initUBot(arg["bot_phone_id"], message.from_user.id)
						return True

					case _:
						result = self.bot.send_message(message.chat.id, f"Не удалось авторизовать аккаунт! Повторите попытку.\n/cancel для отмены")
						arg["delete_messages"].append(result.id)
						self.la.set(message.from_user.id, code, arg)
						return True
				pass


			case 30:
				if (arg["rights"] == "ADMIN"):
					rank = 88
				else:
					rank = 18

				if (message.forward_date != None):
					if (message.forward_from == None):
						result = self.bot.send_message(message.chat.id, "❌  Не удалось достать id пользователя.\nПовторите попытку используя ручной ввод id\n\n/cancel для отмены.")
						arg["delete_messages"].append(result.id)
						arg["delete_messages"].append(message.id)
						self.la.set(message.from_user.id, code, arg)
						return True
					
					self.access.giveAccess(message.forward_from.id, rank)
					await self.db.registerOrUpdateUser(message.forward_from.id, message.forward_from.first_name, message.forward_from.last_name, message.forward_from.username, rank)
				else:
					if (message.text == "/cancel"):
						self.bot.send_message(message.chat.id, "Действие отменено!")
						await self.__start_menu__(message.chat.id, None, self.access.checkAccessLevel(message.from_user.id, 2))
						return True

					try:
						id = int(message.text)
					except:
						result = self.bot.send_message(message.chat.id, "❌  Неверные данные!\nПовторите попытку, введите целое число id пользователя\n\n/cancel для отмены.")
						arg["delete_messages"].append(result.id)
						arg["delete_messages"].append(message.id)
						self.la.set(message.from_user.id, code, arg)
						return True

					self.access.giveAccess(id, rank)
					await self.db.registerUserOrUpdateRank(id, "???", None, "???", rank)

				arg["delete_messages"].append(message.id)

				for id in arg["delete_messages"]:
					try:
						self.bot.delete_message(message.chat.id, id)
					except:
						pass

				await self.__access_list_page__(message.chat.id, message.from_user.id, arg["update_message"], 0, True)
				return True
			
			
			case _:
				self.la.set(message.from_user.id, code, arg)
				return False
				pass
		pass





	################
	#							 ####
	#	Callback handler:		###
	#							 ####
	################				
	async def __callback_handler_async__(self, data):
		print("Callback triggered: ", data.data)
		
		command = data.data.split(' ')[0]
		update_message = data.message.id
		last_action = self.la.get(data.from_user.id)

		match (command):
			case "menu":
				await self.__start_menu__(data.message.chat.id, data.message.id, self.access.checkAccessLevel(data.from_user.id, 2))

			case "new_bot":
				message_id = self.send_response(data.message.chat.id, "Введите номер телефона в международном формате вместе с кодом страны.")
				arg = {
					"delete_messages": [message_id]
				}
				self.la.set(data.from_user.id, 1, arg)
				pass

			case "my_bots":
				message_id = self.send_response(data.message.chat.id, "Coming soon...")
				pass


			#
			#	Access actions:
			#
			case "access":
				page = 0
				if (last_action and last_action["code"] == 100):
					page = last_action["arg"]["page"]
				await self.__access_list_page__(data.message.chat.id, data.from_user.id, update_message, page)
				pass

			case "user":
				if (not last_action):
					return
				arg = int(data.data.split(' ', 1)[1])
				if (last_action and last_action["code"] == 100):
					await self.__show_user__(data.message.chat.id, arg, update_message)
				self.la.set(data.from_user.id, last_action["code"], last_action["arg"])
				pass

			case "give_access":
				if (data.data.find(' ') != -1):
					arg = data.data.split(' ', 1)[1]
					result = self.bot.send_message(data.from_user.id, "<b>Для предостовления доступа, отправьте id человека, или перешлите любое сообщение от него</b>\n\n<i>/cancel для отмены.</i>", "html")
					self.la.set(data.from_user.id, 30, {"delete_messages": [result.id], "update_message": update_message, "rights": arg})
				else:
					text = "<b>Выберете предоставляемые права:</b>"
					btns = telebot.types.InlineKeyboardMarkup()
					btns.add(
								telebot.types.InlineKeyboardButton("Admin", None, "give_access ADMIN"),
								telebot.types.InlineKeyboardButton("User", None, "give_access USER")
							)
					self.send_response(data.message.chat.id, text, btns, update_message)
					pass
				pass

			case "dismiss":	#	page
				if (not last_action):
					return
				if (last_action["code"] != 100):
					return

				args = data.data.split(' ', 2)
				if (len(args) >= 2):
					user_id = int(args[1])
				if (len(args) >= 3):
					is_aproved = True
				else:
					is_aproved = False

				if (is_aproved):
					self.access.dismiss(user_id)
					await self.db.updateUserRank(user_id)
					await self.__access_list_page__(data.message.chat.id, data.from_user.id, update_message, last_action["arg"]["page"])
				else:
					await self.__show_user__(data.message.chat.id, user_id, update_message, True)
				self.la.set(data.from_user.id, last_action["code"], last_action["arg"])
				pass



			#
			#	Page builder:
			#
			case "prev_page":
				if (not last_action):
					return
				if (last_action["code"] == 100):
					await last_action["arg"]["page_func"](last_action["arg"]["chat_id"], data.from_user.id, update_message, last_action["arg"]["page"] - 1)
				else:
					self.la.set(data.from_user.id, last_action["code"], last_action["arg"])
				pass

			case "next_page":
				if (not last_action):
					return
				if (last_action["code"] == 100):
					await last_action["arg"]["page_func"](last_action["arg"]["chat_id"], data.from_user.id, update_message, last_action["arg"]["page"] + 1)
				else:
					self.la.set(data.from_user.id, last_action["code"], last_action["arg"])
				pass

		pass

   
	




	################         ##
	#                       ##
	#   Text handler        #
	#
	################
	async def __text_handler__(self, message):
		if (not self.access.check(message.from_user.id)):
			return False
		if (self.access.needUpdate(message.from_user.id)):
			new_rank = self.access.getRank(message.from_user.id) + 1
			await self.db.registerOrUpdateUser(
												message.from_user.id, 
												message.from_user.first_name, 
												message.from_user.last_name, 
												message.from_user.username, 
												new_rank
											)
			self.access.updateRank(message.from_user.id, new_rank)
			print("User registered")
		print("Bot recieved: ", message.text, "\nFrom user:", message.from_user.id)

		if (message.reply_to_message):
			await self.__reply_handler__(message)
			return True

		command = message.text.split(' ')[0]

		match (command):
			case "/start":
				await self.__start_menu__(message.chat.id, None, self.access.checkAccessLevel(message.from_user.id, 2))

			case "/help":
				self.send_response(message.chat.id, "/start\n/help\n/hard_stat")
				pass

			case "/hard_stat":
				if (self.access.checkAccessLevel(message.from_user.id, 2)):
					await self.__send_hard_stat__(message.chat.id)
				else:
					self.send_response(message.chat.id, "У вас недостаточно прав для выполнения этой команды!")
				pass


		return True



	async def __reply_handler__(self, message):
		message_assoctiation = await self.db.getAssociationInfo(message.reply_to_message.id, message.from_user.id)
		if (not message_assoctiation):
			return
		await self.uBots.sendResponse(message_assoctiation.bot_phone_id, 
								message_assoctiation.sender_id, 
								message_assoctiation.sender_msg_id, 
								message.text,
								message_assoctiation.str_sender_id,
								True if message_assoctiation.status == 2 else False)
		#	Вызываем асинхронное обновление сообщений и выходим из фунции (обработчик)
		self.uBots.setAction(lambda : self.uBots.updateUnreadMessages(message_assoctiation.bot_phone_id, None, 60))
		pass



	################
	#
	#	Screens:
	#
	################
	async def __start_menu__(self, chat_id, message_id = None, is_admin = False):
		text = "<b>Меню: </b>"
		btns = telebot.types.InlineKeyboardMarkup()

		btns.add(telebot.types.InlineKeyboardButton("➕  Новый бот", None, "new_bot"))
		btns.add(telebot.types.InlineKeyboardButton("🤖  Мои боты", None, "my_bots"))
		if (is_admin):
			text += "    <i>Admin</i>"
			btns.add(telebot.types.InlineKeyboardButton("🫂  Доступ", None, "access"))

		self.send_response(chat_id, text, btns, message_id)
		pass



	#
	#	Processing new messages:
	#
	async def processNewMessages(self, sender_object, bot_phone_id, bot_user_id, owner):
		await self.db.newSender(sender_object["from"]["id"], sender_object["from"]["username"])
		asyncio.create_task(self.__notifyAboutMessages__(sender_object, bot_phone_id, bot_user_id, owner))
		pass

	async def __notifyAboutMessages__(self, sender_object, bot_phone_id, bot_user_id, owner):	# private (типа)
		text = (
			"<b>✉️  Получены новые сообщения от пользователя:</b> " +
			f"<a href=\"tg://user?id={sender_object['from']['id']}\">{sender_object['from']['first_name']}</a>" +
			f"{' (@' + sender_object['from']['username'] + ')' if sender_object['from']['username'] else ''}\n\n"
			f"🤖  Получены ботом: <a href=\"tg://user?id={bot_user_id}\">{bot_phone_id}</a>\n\n" +
			"<i>Для ответа на сообщение, ответьте (сдвиньте влево) на интересующее сообщение:</i>\n\n" +
			"<b>Сообщения предоставлены ниже: ⬇️</b>"
		)
		self.bot.send_message(owner, text, "html", disable_web_page_preview=True)
		sender_object["messages"].reverse()
		for msg in sender_object["messages"]:
			if (msg["type"] == "TEXT"):
				result = self.bot.send_message(owner, 
												f"<a href=\"tg://user?id={sender_object['from']['id']}\">{sender_object['from']['first_name']}:</a>\n"
												+ msg["text"], "html",
												disable_web_page_preview=True)
			elif (msg["type"] == "PHOTO"):
				result = self.bot.send_photo(owner, telebot.types.InputFile(msg["file_name"]), msg["caption"])
			await self.db.updateAssociationStatus(bot_phone_id, sender_object['from']['id'], 2)
			await self.db.newAssociation(bot_phone_id, sender_object['from']['id'], msg["id"], result.id, 1)
			pass
		pass




	#####################
	#	Notify for owner:
	#
	async def notifyAbouBrokeBot(self, owner, broken_bot_phone_id):
		# bot_info = await self.db.getBotInfo(broken_bot_phone_id)
		text = ""
		text += f"Бота {broken_bot_phone_id} невозможно запустить!\n"
		text += f"\n"
		text += f"Проверьте аккаунт на валидность и при необходимости добавьте аккаунт еще раз\n"
		text += f"Аккаунт отключён.\n"
		self.send_response(owner, text)
		pass

	async def notifyForAdminsAboutBrokenProxy(self, broken_proxy_hostnames: list):
		text = ""
		text += "❗️  Стоит проверить прокси сервера!\nСистема обнаружила, что через прокси ниже не удаётся подключиться к интеренету:\n<b>Адреса:</b>"
		hostnames_in_message = 100
		hostnames_len = len(broken_proxy_hostnames)
		counter = 0
		for i in range((hostnames_len // hostnames_in_message)):
			for hostname in broken_proxy_hostnames:
				if (hostnames_len <= 0):
					break
				if (counter >= hostnames_in_message):
					for user in self.access.list():
						if (self.access.checkAccessLevel(user.user_id, 2)):
							self.send_response(user.user_id, text)
							text = ""
							counter = 0
							pass
				text += f"<code>{hostname}</code>"
				counter += 1
				hostnames_len -= 1
				
		pass




	#
	#	Access screen;
	#
	async def __access_list_page__(self, chat_id, from_user, message_id = None, page = 0, new_user_added = False):
		white_list = await self.db.getWhiteList()

		text = "🔺  -  Root\n🔸  -  Admin\n🔹  -  User"
		if (new_user_added):
			text += "\n\nНовый пользователь успешно добавлен!" 
		btns_info = []

		for user in white_list:
			info = {
				"text": "",
				"callback_data": ""
			}
			
			if (user.rank >= 90):
				info["text"] += "🔺  "
			elif (user.rank >= 80):
				info["text"] += "🔸  "
			else:
				info["text"] += "🔹  "

			info["text"] += user.full_name
			if (from_user == user.user_id):
				info["text"] += "  (You)"	
			elif (user.username):
				info["text"] += "  (@" + user.username + ")"
			
			info["callback_data"] = "user " + str(user.user_id)
			btns_info.append(info)
			pass

		btns = self.__build_btns_page__(btns_info, page, 5, [telebot.types.InlineKeyboardButton("➕  Предоставить доступ", None, "give_access"),
						       								telebot.types.InlineKeyboardButton("🏠  Меню", None, "menu")])

		self.send_response(chat_id, text, btns, message_id)
		self.la.set(from_user, 100, {
			"chat_id": chat_id,
			"page": page,
			"page_func": self.__access_list_page__
		})
		pass 

	async def __show_user__(self, chat_id, id, message_id = None, is_dismiss = False):
		text = ""
		btns = telebot.types.InlineKeyboardMarkup()

		user = await self.db.getUserInfo(id)

		text += "<a href=\"tg://user?id=" + str(user.user_id) + "\">" + user.full_name + "</a>\n"
		text += "<b>Id: </b>" + str(user.user_id) + "\n"
		if (user.username):
			text += "<b>Username: </b>@" + user.username  + "\n"
		text += "<b>Права: </b>"

		if (user.rank >= 90):
			text += "🔺 Root"
		elif (user.rank >= 80):
			text += "🔸 Admin"
		else:
			text += "🔹 User"

		if (user.rank < 90):
			if (not is_dismiss):
				btns.add(telebot.types.InlineKeyboardButton("🛑  Отобрать доступ", None, f"dismiss {id}"))
			else:
				btns.add(telebot.types.InlineKeyboardButton("🛑  Отобрать доступ", None, f"dismiss {id} delete"), telebot.types.InlineKeyboardButton("❌  Отменить", None, "user " + str(id)))
		btns.add(telebot.types.InlineKeyboardButton("🔙  Назад", None, "access"))
		
		self.send_response(chat_id, text, btns, message_id)
		pass





	###################
	#	Statistic:
	async def __send_hard_stat__(self, chat_id):
		text = ""
		text += f"Доступ к боту имеют: {self.access.count()}\n"
		text += f"\n"
		text += f"Общее кол-во ботов: {await self.db.getBotsCount()}\n"
		text += f"Кол-во запущеных ботов: {len(self.uBots.loaded_sessions)}\n"
		text += f"Одновременно может быть запущено ботов: {self.uBots.max_loaded_sessions}\n"
		text += f"\n"
		text += f"Общее кол-во прокси: {self.uBots.proxys.count(deactived_also=True)}\n"
		text += f"Кол-во доступных прокси: {self.uBots.proxys.count()}\n"
		try:
			self.send_response(chat_id, text)
		except:
			pass
		pass



	#
	#	Other methods:
	#
	def send_response(self, chat_id, text, btns = None, message_id = None):
		if message_id:
			try:
				self.bot.edit_message_text(text, chat_id, message_id, parse_mode="html", reply_markup=btns)
				return message_id
			except:
				pass
		else:
			message_id = self.bot.send_message(chat_id, text, "html", reply_markup=btns).id
			return message_id
		pass

	def __build_btns_page__(self, btns_info, page, max_btns_one_page = 5, insert_down: list = [], show_current_page = True):
		#
		#	btns_info = [
		# 		{
		#			text:
		#			callback_data:
		#		}
		#	]
		#
	
		ret = telebot.types.InlineKeyboardMarkup()
		skip = page * max_btns_one_page
		max_page = len(btns_info) // (max_btns_one_page + 1)
		down_line_btns = ()
		iter = 0
	

		for btn in btns_info:
			if (skip > 0):
				skip -= 1
				continue
			ret.add(telebot.types.InlineKeyboardButton(btn["text"], None, btn["callback_data"]))
			iter += 1
			if iter >= max_btns_one_page:
				break

		if (page > 0):
			down_line_btns += (telebot.types.InlineKeyboardButton("<", None, "prev_page"), )

		if (show_current_page):
			down_line_btns += (telebot.types.InlineKeyboardButton(f"{page + 1}/{max_page + 1}", None, "None"), )
		
		if (page < max_page):
			down_line_btns += (telebot.types.InlineKeyboardButton(">", None, "next_page"), )

		ret.add(*down_line_btns)
		for insert in insert_down:
			ret.add(insert)

		return ret

	pass