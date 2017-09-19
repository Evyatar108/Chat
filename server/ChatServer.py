import logging
import select
import socket
import ssl
import sys
from server.Client import Client


logger = logging.getLogger('server logger')
logging.basicConfig(level=logging.DEBUG)
clients= {}
usedNicks=[]
banList=[]
HOST = ''
PORT = 52441
raw_server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
raw_server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
raw_server.bind((HOST,PORT))
raw_server.listen(100)
context = ssl.create_default_context(Purpose=ssl.Purpose.CLIENT_AUTH)
context.set_ciphers('EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH')
server = context.wrap_socket(sock=raw_server,server_side=True)
logger.info('Listening on {}:{}'.format(HOST,PORT))
epoll = select.epoll()
epoll.register(server,select.POLLIN)
epoll.register(sys.stdin,select.POLLIN)
logger.info('Started epoll')

def acceptNewClient(count,banList):
	clientSock,addr = server.accept()
	if addr[0] in banList:
		logger.info('{} is banned yet tried to connect'.format(addr[0]))
	else:
		logger.info('{} connected'.format(addr))
		clientSock.setblocking(False)
		epoll.register(clientSock,select.POLLIN)
		nick='guest{}'.format(count)
		client = Client(sock=clientSock, addr=addr, nick=nick)
		usedNicks.append(nick)
		clients[client.fileno()] = client

def broadcast(msg):
	text = '{}: {}'.format(msg.getNick(),msg.getContent())
	logger.info('IP: {} Nick: {} Message: {}'.format(msg.getAddr(),msg.getNick(),msg.getContent()))
	for client in clients.values():
		sendText(client,text)

def broadcastAll(msgs):
	for msg in msgs:
		broadcast(msg)

def sendText(client,text):
	client.appendData(text.encode('utf-8') + b'\0')
	epoll.modify(client.fileno(), select.POLLOUT)

def sendData(client):
	logger.debug('sending data to: {}'.format(client.getNick()))
	client.sendData()
	if client.synced():
		epoll.modify(client.fileno(),select.POLLIN)

def disconnect(client):
	logger.info('{} disconnected'.format(client.getAddr()))
	fileno = client.fileno()
	epoll.unregister(fileno)
	del clients[fileno]
	client.close()
	usedNicks.remove(client.getNick())

def loadBanned():
	banned=[]
	with open('banned.txt','r') as file:
		for line in file:
			banned.append(line.rstrip('\n'))
	return banned

def saveBanned():
	with open('banned.txt','w') as file:
		for ip in banList:
			file.write(ip+'\n')


def handleMsgs(client,msgs):
	procMsgs = []
	for msg in msgs:
		if isCommand(msg):
			handleCommand(client,msg.getContent())
		else:
			procMsgs.append(msg)

	return procMsgs

def isCommand(msg):
	return msg.getContent()[0] is '/'

def handleCommand(client,command):
	command = command[1:]
	words = command.split(' ')
	if len(words)>0:
		if words[0] is 'nick':
			changeNickCommand(client,words[1:])
		#elif words[0] is 'pm':
			#privateMsg(client,words[1:]# )
		elif client.isAdmin():
			handleAdminCommand(words)


def changeNickCommand(client,words):
	#TODO update after implementing users, change nick only for registered users
	if len(words) > 0:
		nick = words[0]
		if len(nick) <= 32:
			if nick not in usedNicks:
				usedNicks.remove(client.getNick)
				client.setNick(nick)
				usedNicks.append(nick)
			else:
				sendText(client, 'this nickname is already being used')
		else:
			sendText(client, 'this nickname is too long (|nickname|>32)')
	else:
		sendText(client, 'Please specify desired nickname')

def handleConsoleInput():
	line = sys.stdin.readline()
	words= line.split(' ')
	handleAdminCommand(words)
	return

def handleAdminCommand(words):
	if len(words) > 0:
		if words[0] is 'ban':
			if len(words) > 1:
				ban(words[1])
			else:
				print('please specify an ip to ban')
		elif words[0] is 'uban':
			if len(words) > 1:
				unban(words[1])
			else:
				print('please specify an ip to uban')

def unban(ip):
	if ip in banList:
		banList.remove()
		saveBanned()
	else:
		print('{} is not banned'.format(ip))

def ban(nick):
	for client in clients:
		if client.getNick() is nick:
			banList.append(client.getAddr()[0])
	saveBanned()

def kick(nick):
	#TODO
	return

def register(client,msg):
	# TODO implement current used nick registering using password
	return

def login(client, msg):
	#msg.getContent() will be of the form "/login *username* *password*"
	#client program will have a special window to safely login without sending it in the chat
	#TODO implement login, change current nick to the registered one
	return

def loadUserList():
	#TODO load userlist from a file
	return

def saveUserList():
	#TODO save userlist into a file
	return

def privateMsg(client,words):
	#TODO
	return


def run():
	userCount=1
	banList=loadBanned()
	while True:
		events = epoll.poll()
		for fileno,event in events:
			if fileno == sys.stdin.fileno():
				handleConsoleInput()
			if fileno == server.fileno():
				logger.debug('server event: {}'.format(event) )
				acceptNewClient(userCount)
				userCount+=1
			else:
				client = clients[fileno]
				logger.debug('event: {} user: {}'.format(event,client.getNick()))
				if event in (select.POLLHUP,select.POLLERR ,select.POLLNVAL):
					disconnect(client)
				if event==select.POLLIN:
					msgs=client.recvMsgs()
					if msgs is not None:
						Client.logger.debug('recieving messages from {}'.format(client.getAddr()))
						msgs=handleMsgs(client,msgs)
						broadcastAll(msgs)
					else:
						disconnect(client)
				if event==select.POLLOUT:
					sendData(client)


if __name__ == '__main__':
	run()