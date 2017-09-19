import logging
import sys
import time
from collections import deque

from Message import Message


class Client:
	logger = logging.getLogger('client logger')
	MAX_LAST_MSGS=50
	MAX_BUFFER_SIZE=4096

	def __init__(self,sock,addr,nick):
		self.__sock=sock
		self.__addr=addr
		self.__toSend=deque()
		self.__buffer=bytes()
		self.__nick=nick
		self.__lastMsgs=deque(maxlen=Client.MAX_LAST_MSGS)

	def __parseMsgs(data):
		chunks = data.split(b'\0')
		msgs = chunks[:-1]
		rest = chunks[-1]
		msgs = [msg.decode('utf-8') for msg in msgs]
		return (msgs, rest)

	def recvMsgs(self):
		data =  self.__sock.recv(4096)
		msgs=None
		if data:
			raw_msgs, self.__buffer= Client.__parseMsgs(self.__buffer + data)
			msgs = [Message(nick=self.getNick(),content=msg,time=time.time()) for msg in msgs]
			for msg in msgs:
				self.__lastMsgs.appendleft(msg)
			self.checkSpam()
		return msgs

	def checkSpam(self):
		if sys.getsizeof(self.__buffer)>Client.MAX_BUFFER_SIZE:
			self.__buffer=bytes()

	def appendData(self,msg):
		self.__toSend.append(msg)
		return self

	def sendData(self):
		data = self.__toSend.popleft()
		sent = self.__sock.send(data)
		if sent < len(data):
			unsentData = data[sent:]
			self.__toSend.appendleft(unsentData)
		return self

	def synced(self):
		return not self.__toSend

	def fileno(self):
		return self.__sock.fileno()

	def close(self):
		self.__sock.close()

	def getAddr(self):
		return self.__addr

	def getNick(self):
		return self.__nick

	def setNick(self,nick):
		self.__nick=nick
		return self