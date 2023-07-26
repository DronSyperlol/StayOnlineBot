class UserInfo:
	def __init__(self, user_id, full_name, username, rank) -> None:
		self.user_id = user_id
		self.full_name = full_name
		self.username = username
		self.rank = rank
		pass
	pass

class BotInfo:
	def __init__(self, bot_phone_id, owner, proxy_hostname, next_login) -> None:
		self.bot_phone_id = bot_phone_id
		self.owner = owner
		self.proxy_hostname = proxy_hostname
		self.next_login = next_login
		pass

class AssociationInfo:
	def __init__(self, bot_phone_id, sender_id, str_sender_id, sender_msg_id, status) -> None:
		self.bot_phone_id = bot_phone_id
		self.sender_id = sender_id
		self.str_sender_id = str_sender_id
		self.sender_msg_id = sender_msg_id
		self.status = status
		pass


class ProxyStat:
	def __init__(self, hostname, bots_quantity):
		self.hostname = hostname
		self.bots_quantity = bots_quantity
		pass