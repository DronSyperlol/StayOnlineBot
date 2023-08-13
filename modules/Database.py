from modules.MySql import Pool
#import asyncio
from modules.Structs import UserInfo, BotInfo, AssociationInfo, ProxyStat



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


	async def getUserInfo(self, user_id) -> UserInfo:
		db_query = "SELECT * FROM `users` WHERE `user_id` = ?"
		result = await self.pool.execute(db_query, [user_id])
		if (len(result) == 0):
			return None
		return UserInfo(result[0][0], result[0][1], result[0][2], result[0][3])
		pass


	async def getWhiteList(self) -> list[UserInfo]:
		db_query = "SELECT * FROM `users` WHERE `rank` > 0"
		result = await self.pool.execute(db_query)
		ret = []
		for row in result:
			ret.append(UserInfo(row[0], row[1], row[2], row[3]))
		return ret
	
	


	#	bots:
	async def newBot(self, bot_phone_id, owner, proxy_hostname, next_login):
		db_query = "INSERT INTO bots(`bot_phone_id`, `owner`, `proxy_hostname`, `next_login`) VALUES (?, ?, ?, ?) ON DUPLICATE KEY UPDATE `bot_phone_id` = VALUES(`bot_phone_id`), `owner` = VALUES(`owner`)"
		await self.pool.execute(db_query, [bot_phone_id, owner, proxy_hostname, next_login])
		pass

	async def updateNextLogin(self, bot_phone_id, next_login = None):
		db_query = "UPDATE `bots` SET `next_login` = ? WHERE `bot_phone_id` = ?"
		await self.pool.execute(db_query, [next_login, bot_phone_id])
		pass

	async def getBotsInfoByOwner(self, owner) -> list[BotInfo]:
		db_query = "SELECT `bot_phone_id`, `owner`, `proxy_hostname`, `next_login` FROM `bots` WHERE `owner` = ?"
		result = await self.pool.execute(db_query, [owner])
		ret = []
		for row in result: 
			ret.append(BotInfo(row[0], row[1], row[2], row[3]))
		return ret
	
	async def getBotInfo(self, bot_phone_id) -> BotInfo | None:
		db_query = "SELECT `bot_phone_id`, `owner`, `proxy_hostname`, `next_login` FROM `bots` WHERE `bot_phone_id` = ?"
		result = await self.pool.execute(db_query, [bot_phone_id])
		if (len(result) == 0):
			return None
		return BotInfo(result[0][0], result[0][1], result[0][2], result[0][3])

	async def getNearestNextLoginBots(self) -> list[BotInfo]:
		db_query = "SELECT `bot_phone_id`, `owner`, `proxy_hostname`, `next_login` FROM `bots` WHERE `next_login` < UNIX_TIMESTAMP()"
		result = await self.pool.execute(db_query)
		ret = []
		for row in result:
			ret.append(BotInfo(row[0], row[1], row[2], row[3]))
			pass
		return ret

	async def getBotOwner(self, bot_phone_id):
		db_query = "SELECT `owner` FROM `bots` WHERE `bot_phone_id` = ?"
		result = await self.pool.execute(db_query, [bot_phone_id])
		return result[0][0]
	
	
	async def getProxyStat(self) -> list[ProxyStat]:
		db_query = "SELECT `proxy_hostname`, COUNT(bot_phone_id) FROM `bots` WHERE `proxy_hostname` IS NOT NULL GROUP BY `proxy_hostname`"
		result = await self.pool.execute(db_query)
		ret = []
		for row in result:
			ret.append(ProxyStat(row[0], row[1]))
		return ret
	
	async def getBotsCount(self) -> int:
		db_query = "SELECT COUNT(*) FROM `bots`"
		result = await self.pool.execute(db_query)
		return result[0][0]
	
	async def delBot(self, bot_phone_id):
		db_query = "DELETE FROM `bots` WHERE `bot_phone_id` = ?"
		await self.pool.execute(db_query, [bot_phone_id])
		pass
	


	# message_association:
	async def newAssociation(self, bot_phone_id, sender_id, sender_msg_id, bot_msg_id, status):
		db_query = "INSERT INTO `message_association` VALUES(?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE `sender_id` = VALUES(`sender_id`)"
		await self.pool.execute(db_query, [bot_phone_id, sender_id, sender_msg_id, bot_msg_id, status])
		pass

	async def updateAssociationStatus(self, bot_phone_id, sender_id, new_status):
		db_query = "UPDATE `message_association` SET `status` = ? WHERE `bot_phone_id` = ? AND `sender_id` = ?"
		await self.pool.execute(db_query, [new_status, bot_phone_id, sender_id])
		pass

	async def getAssociationInfo(self, bot_msg_id, bot_owner) -> AssociationInfo:
		db_query = "SELECT ma.bot_phone_id, ma.sender_id, s.username as str_sender_id, ma.sender_msg_id, ma.status FROM `message_association` AS ma INNER JOIN `bots` AS b ON ma.bot_phone_id = b.bot_phone_id INNER JOIN `senders` AS s ON ma.sender_id = s.id WHERE b.owner = ? AND ma.bot_msg_id = ?"
		result = await self.pool.execute(db_query, [bot_owner, bot_msg_id])
		if (len(result) == 0):
			return None
		return AssociationInfo(result[0][0], result[0][1], result[0][2], result[0][3], result[0][4])
	
	async def delAssociationsByBot(self, bot_phone_id):
		db_query = "DELETE FROM `bots` WHERE `bot_phone_id` = ?"
		await self.pool.execute(db_query, [bot_phone_id])
		pass


	#	senders:
	async def newSender(self, id, username):
		db_query = "INSERT INTO `senders` VALUES (?, ?) ON DUPLICATE KEY UPDATE `username` = VALUES(`username`)"
		await self.pool.execute(db_query, [id, username])
		pass

	async def getSenderUsername(self, id):
		db_query = "SELECT `username` FROM `senders` WHERE `id` = ?"
		result = await self.pool.execute(db_query, [id])
		return result[0][0]

	pass