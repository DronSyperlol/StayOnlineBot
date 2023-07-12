import telebot
from threading import Thread 
import asyncio
from modules.Access import Access
from modules.Database import DataBase
from modules.LastAction import LastAction
from modules.UserBots import UserBots




class Bot:
	def __init__(self, api_key, DBAuthKey, admin_list: list, uBots: UserBots):
		self.bot = telebot.TeleBot(api_key)
		self.db = DataBase(DBAuthKey)
		self.la = LastAction()
		self.uBots = uBots
		
		self.access = Access()
		temp = asyncio.run(self.db.getWhiteList())
		for info in temp:
			rank = ((info["rank"] // 10) * 10) + 7
			self.access.giveAccess(info["user_id"], rank)
		del temp
		for id in admin_list:
			if (not self.access.check(id)):
				self.access.giveAccess(id, 98)
			else:
				self.access.updateRank(id, 98)
			pass
		self.access.initAll()
		
		self.thread = Thread(target=self.__thread_target__)
		self.thread.start()
		pass






	def __thread_target__(self):
		self.loop = asyncio.new_event_loop()

		@self.bot.callback_query_handler(self.__callback_handler__)
		

		@self.bot.message_handler()
		def callback_func(message):
			last_action = self.la.get(message.from_user.id)
			if (
				last_action 
				and
				self.loop.run_until_complete(self.__last_action_handler__(message, last_action["code"], last_action["arg"]))
			):
				return
			self.loop.run_until_complete(self.__text_handler__(message))
			pass


		self.bot.infinity_polling()
		pass





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
				phone += message.text

				if (await self.uBots.newBot(phone) == "Waiting code"):
					result = self.bot.send_message(message.chat.id, "Отправьте мне код верификации чтобы я смог авторизовать аккаунт.\nОн уже был отправлен.")
					arg["delete_messages"].append(result.id)
					arg["bot_phone_id"] = int(phone.replace('+', ''))
					self.la.set(message.from_user.id, 2, arg)
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
				pass
		pass





	################
	#							 ####
	#	Callback handler:		###
	#							 ####
	################				
	def __callback_handler__(self, data):
		async def __callback_handler_async__(data):
			print("Callback triggered: ", data.data)
			
			command = data.data.split(' ')[0]
			update_message = data.message.id
			last_action = self.la.get(data.from_user.id)

			match (command):
				case "new_bot":
					message_id = self.send_response(data.message.chat.id, "Введите номер телефона в международном формате вместе с кодом страны.")
					arg = {
						"delete_messages": [message_id]
					}
					self.la.set(data.from_user.id, 1, arg)
					pass

				case "my_bots":
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
					arg = int(data.data.split(' ', 1)[1])
					if (last_action["code"] == 100):
						if ("is_dismiss" in last_action["arg"]):
							self.access.dismiss(arg)
							await self.db.updateUserRank(arg)
							await self.__access_list_page__(data.message.chat.id, data.from_user.id, update_message, last_action["arg"]["page"])
							del last_action["arg"]["is_dismiss"]
						else:
							last_action["arg"]["is_dismiss"] = True
							await self.__show_user__(data.message.chat.id, arg, update_message, True)
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
		self.loop.run_until_complete(__callback_handler_async__(data))
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

		command = message.text.split(' ')[0]

		match (command):
			case "/start":
				await self.__start_menu__(message.chat.id, None, self.access.checkAccessLevel(message.from_user.id, 2))



		return True







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
			
			if (user["rank"] >= 90):
				info["text"] += "🔺  "
			elif (user["rank"] >= 80):
				info["text"] += "🔸  "
			else:
				info["text"] += "🔹  "

			info["text"] += user["full_name"]
			if (from_user == user["user_id"]):
				info["text"] += "  (You)"	
			elif (user["username"]):
				info["text"] += "  (@" + user["username"] + ")"
			
			info["callback_data"] = "user " + str(user["user_id"])
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

		text += "<a href=\"tg://user?id=" + str(user["user_id"]) + "\">" + user["full_name"] + "</a>\n"
		text += "<b>Id: </b>" + str(user["user_id"]) + "\n"
		if (user["username"]):
			text += "<b>Username: </b>@" + user["username"]  + "\n"
		text += "<b>Права: </b>"

		if (user["rank"] >= 90):
			text += "🔺 Root"
		elif (user["rank"] >= 80):
			text += "🔸 Admin"
		else:
			text += "🔹 User"

		if (user["rank"] < 90):
			if (not is_dismiss):
				btns.add(telebot.types.InlineKeyboardButton("🛑  Отобрать доступ", None, "dismiss " + str(id)))
			else:
				btns.add(telebot.types.InlineKeyboardButton("🛑  Отобрать доступ", None, "dismiss " + str(id)), telebot.types.InlineKeyboardButton("❌  Отменить", None, "user " + str(id)))
		btns.add(telebot.types.InlineKeyboardButton("🔙  Назад", None, "access"))
		
		self.send_response(chat_id, text, btns, message_id)
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