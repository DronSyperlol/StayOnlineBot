#	+---------------------------------------------------------------+
#	|	"Stay online bot" aka "Onliner" 							|
#	|	Developer:	Syperlol										|
#	|	Contacts:	t.me/Syperlol github.com/DronSyperlol			|
#	|																|
#	|	Pyrhon 3.11													|
#	+---------------------------------------------------------------+





def main():
	import asyncio
	from configparser import ConfigParser
	from modules.Bot import Bot
	from modules.Database import DataBaseAuthKey
	from modules.UserBots import UserBots



	#	Consts:
	CONFIG_FILE = "./data/config.cfg"



	#	Starting:
	#	#	Read config
	config = ConfigParser()
	config.read(CONFIG_FILE)
	

	#	#	Init DB Key:
	db_key = DataBaseAuthKey(
		config["database"]["MYSQL_HOST"],
		config["database"]["MYSQL_PORT"],
		config["database"]["MYSQL_USER"],
		config["database"]["MYSQL_PASSWORD"],
		config["database"]["MYSQL_DATABASE"]
	)
	

	admin_list = config["bot"]["ADMINS"].split(', ')
	admin_list = [int(id) for id in admin_list]
	

	#	#	Init user bots:
	uBots = UserBots(
					config["paths"]["SESSIONS_PATH"], 
					db_key, 
					config["telegram"]["API_ID"], 
					config["telegram"]["API_HASH"]
				)


	#	#	Init and start bot
	bot = Bot(
				config["telegram"]["BOT_TOKEN"], 
				db_key, 
				admin_list,
				uBots
			)


	#	Clear memory:
	del db_key
	del config


	async def async_main():
		while (True):
			await asyncio.sleep(5)
		pass

	asyncio.run(async_main())
	pass



if (__name__ == "__main__"):
	main()