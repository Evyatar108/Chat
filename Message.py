import time
class Message:

	def __init__(self,nick,content):
		self.__nick = nick
		self.__content = content
		self.__time = time.time()

	def getContent(self):
		return self.__content

	def getTime(self):
		return self.__time

	def getNick(self):
		return self.__nick
