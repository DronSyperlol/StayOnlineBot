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
	


	pass