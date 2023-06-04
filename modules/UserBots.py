from modules.UserBot import UserBot 
from modules.Database import DataBase

class UserBots:
	def __init__(self, session_directory, DBAuthKey, api_id, api_hash):
		self.bots = []
		self.session_directory = session_directory
		self.db = DataBase(DBAuthKey)
		self.api_id = api_id
		self.api_hash = api_hash


	async def newBot(self, phone: str):
		session_name = f"tmp_{phone.replace('+', '')}"

		bot = UserBot(self.session_directory, session_name, None, self.api_id, self.api_hash)
		bot.start()
		
		return await bot.doLogin(phone)
		
	pass