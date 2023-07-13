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
	from os.path import exists
	from os import mkdir


	#	Def functinons:
	def create_dirs(config):
		if (not exists(config["paths"]["SESSIONS_PATH"])):
			mkdir(config["paths"]["SESSIONS_PATH"])
		pass

	async def status_updater(uBots: UserBots, timeout):
		while True:
			await uBots.checkNextLogins()
			await asyncio.sleep(timeout)
			pass
		pass

	async def bot_life_checker(uBots: UserBots, timeout):
		while True:
			await uBots.killOldUBots()
			await asyncio.sleep(timeout)
			pass
		pass


	#	Consts:
	CONFIG_FILE = "./data/config.cfg"



	#	Starting:
	#	#	Read config
	config = ConfigParser()
	config.read(CONFIG_FILE)


	#	Creating dirs:
	create_dirs(config)
	

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
					config["telegram"]["API_HASH"],
					int(config["bot"]["NEXT_LOGIN_LOWER_THRESHOLD"]),
					int(config["bot"]["NEXT_LOGIN_UPPER_THRESHOLD"])
				)


	#	#	Init and start bot
	bot = Bot(
				config["telegram"]["BOT_TOKEN"], 
				db_key, 
				admin_list,
				uBots
			)

	uBots.setCallbacks(bot.notifyAboutMessages)

	#	Clear memory:
	del db_key


	async def async_main(config):
		updater_task = asyncio.create_task(status_updater(uBots, int(config["bot"]["UPDATER_ONLINE_TIMEOUT"])))
		bot_killer_task = asyncio.create_task(bot_life_checker(uBots, int(config["bot"]["KILL_OLD_BOTS_TIMEOUT"])))

		await updater_task
		await bot_killer_task
		pass

	asyncio.run(async_main(config))
	pass



if (__name__ == "__main__"):
	main()