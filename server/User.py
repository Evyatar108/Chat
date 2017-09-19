

class User:

	def __init__(self,uid,nick,username,password):
		self.__username=username
		self.__nick=nick
		self.__password = password #sent salted and hashed by the client
		self.__banned=False
		self.__IPs=[]
		self.__isAdmin = False

	def getNick(self):
		return self.__nick

	def setAdmin(self,flag):
		self.__isAdmin=flag
		return self

	def getUsername(self):
		return self.__username

	def setNick(self,nick):
		self.__nick=nick
		return self

	def ban(self):
		self.__banned=True
		return self

	def unban(self):
		self.__banned=False
		return self

	def addIP(self,ip):
		self.__IPs.append(ip)
		return self

