import telebot
from threading import Thread 
import asyncio
from modules.Access import Access
from modules.Database import DataBase
from modules.LastAction import LastAction




class Bot:
	def __init__(self, api_key, DBAuthKey, admin_list: list):
		self.bot = telebot.TeleBot(api_key)
		self.db = DataBase(DBAuthKey)
		self.la = LastAction()
		
		self.access = Access()
		temp = asyncio.run(self.db.getWhiteList())
		for info in temp:
			rank = ((info["rank"] // 10) * 10) + 7
			self.access.giveAccess(info["user_id"], rank)
		del temp
		for id in admin_list:
			if (not self.access.check(id)):
				self.access.giveAccess(id, 98)
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
			self.loop.run_until_complete(self.__text_handler__(message))
			pass


		self.bot.infinity_polling()
		pass


	################
	#							 ####
	#	Callback handler:		###
	#							 ####
	################				
	async def __callback_handler__(self, data):
		async def __callback_handler_async__(data):
			print("Callback triggered: ", data.data)
			
			command = data.data.split(' ')[0]
			update_message = data.message.id
			last_action = self.la.get(data.from_user.id)

			match (command):
				case "add_bot":
					pass

				case "my_bots":
					pass

				case "access":
					self.__access_list_page__(data.message.chat.id, data.from_user.id, update_message)
					pass


				case "prev_page":
					if (not last_action):
						return
					if (last_action["code"] == 100):
						await last_action["arg"]["page_func"](last_action["arg"]["chat_id"], data.from_user.id, self.update_message_id[data.message.chat.id], last_action["arg"]["page"] - 1)
					else:
						self.la.set(data.from_user.id, last_action["code"], last_action["arg"])
					pass

				case "next_page":
					if (not last_action):
						return
					if (last_action["code"] == 100):
						await last_action["arg"]["page_func"](last_action["arg"]["chat_id"], data.from_user.id, self.update_message_id[data.message.chat.id], last_action["arg"]["page"] + 1)
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
		text = "Меню: "
		btns = telebot.types.InlineKeyboardMarkup()

		btns.add(telebot.types.InlineKeyboardButton("➕  Добавить бота", None, "add_bot"))
		btns.add(telebot.types.InlineKeyboardButton("🤖  Мои боты", None, "my_bots"))
		if (is_admin):
			btns.add(telebot.types.InlineKeyboardButton("🫂  Доступ", None, "access"))

		self.send_response(chat_id, text, btns, message_id)
		pass





	async def __access_list_page__(self, chat_id, from_user, message_id = None, page = 0, new_user_added = False):
		white_list = await self.db.getWhiteList()

		text = "🔺  -  Root\n🔸  -  Admin\n🔹  -  Just user (not used)"
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




	#
	#	Other methods:
	#
	def send_response(self, chat_id, text, btns = None, message_id = None):
		if message_id:
			try:
				self.bot.edit_message_text(text, chat_id, message_id, parse_mode="html", reply_markup=btns)
			except:
				pass
		else:
			self.bot.send_message(chat_id, text, "html", reply_markup=btns)
		pass
	pass