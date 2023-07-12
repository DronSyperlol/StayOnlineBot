from modules.MySql import Pool
#import asyncio



class DataBaseAuthKey:
	def __init__(self, host, port, user, password, database):
		self.host=host
		self.port=port
		self.user=user
		self.password=password
		self.database=database
		pass
	pass


class DataBase:
	def __init__(self, auth_key: DataBaseAuthKey) -> None:
		self.pool = Pool(auth_key.host, auth_key.port, auth_key.user, auth_key.password, auth_key.database, 5)
		pass



	#	`Users`
	async def registerOrUpdateUser(self, user_id, first_name, last_name, username, rank):
		db_query = "INSERT INTO `users` VALUES(?, ?, ?, ?) ON DUPLICATE KEY UPDATE `full_name` = VALUES(`full_name`), `username` = VALUES(`username`), `rank` = VALUES(`rank`)"
		if (last_name):
			first_name += f" {last_name}"
		await self.pool.execute(db_query, [user_id, first_name, username, rank])
		pass

	
	async def registerUserOrUpdateRank(self, user_id, first_name, last_name, username, rank):
		db_query = "INSERT INTO `users` VALUES(?, ?, ?, ?) ON DUPLICATE KEY UPDATE `rank` = VALUES(`rank`)"
		if (last_name):
			first_name += f" {last_name}"
		await self.pool.execute(db_query, [user_id, first_name, username, rank])
		pass


	async def updateUserRank(self, user_id, rank = 0):
		db_query = "UPDATE `users` SET `rank` = ? WHERE `user_id` = ?"
		await self.pool.execute(db_query, [rank, user_id])
		pass


	async def getUserInfo(self, user_id):
		db_query = "SELECT * FROM `users` WHERE `user_id` = ?"
		result = await self.pool.execute(db_query, [user_id])
		return {
			"user_id": result[0][0],
			"full_name": result[0][1], 
			"username": result[0][2],
			"rank": result[0][3]
		}
		pass


	async def getWhiteList(self):
		db_query = "SELECT * FROM `users` WHERE `rank` > 0"
		result = await self.pool.execute(db_query)
		ret = []
		for row in result:
			ret.append({
				"user_id": row[0],
				"full_name": row[1],
				"username": row[2],
				"rank": row[3]
			})
		return ret
	
	


	#	bots:
	async def newBot(self, bot_phone_id, owner, next_login):
		db_query = "INSERT INTO bots VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE `bot_phone_id` = VALUES(`bot_phone_id`), `owner` = VALUES(`owner`)"
		await self.pool.execute(db_query, [bot_phone_id, owner, next_login])
		pass

	async def updateNextLogin(self, bot_phone_id, next_login = None):
		db_query = "UPDATE `bots` SET `next_login` = ? WHERE `bot_phone_id` = ?"
		await self.pool.execute(db_query, [next_login, bot_phone_id])
		pass

	async def getNearestNextLoginBots(self):
		db_query = "SELECT * FROM `bots` WHERE `next_login` < UNIX_TIMESTAMP()"
		result = await self.pool.execute(db_query)
		ret = []
		for row in result:
			ret.append({
				"bot_phone_id": row[0],
				"owner": row[1], 
				"next_login": row[2]
			})
			pass
		pass
	pass