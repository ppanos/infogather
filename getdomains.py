__author__ = 'panos'
from sys import exit, argv, stdout
from termcolor import colored
from socket import gethostbyname, gaierror, socket, error
from os.path import basename, isfile
from os import remove, system, name
from os import error as os_error
from urllib import urlencode
from httplib2 import ProxyInfo, Http, HttpLib2Error
from httplib2.socks import PROXY_TYPE_SOCKS4
from json import loads
from time import sleep
from re import compile, IGNORECASE,VERBOSE, search
domain_counter = 0
# user defined variables
debug = 1
tor_host = '127.0.0.1'
tor_port = 9050
tor_control_port = 9051

def out(message,level):
	global debug, domain_counter
	if level == 1:
		prefix = '[-] Fatal: '
		collor = 'red'
	elif level == 2:
		prefix = '[*] Note: '
		collor = 'yellow'
	elif level == 3:
		prefix = '[+] OK: '
		collor = 'green'
	elif level == 4:
		prefix = '[x] Info: '
		collor = 'magenta'
	elif level == 5:
		prefix = '[+] Total domain count: '
		collor = 'green'
	else:
		raise ValueError
	if len(message) == 0:
		raise ValueError
	if level == 3 and 'found.' in message:
		domain_counter += 1
	if debug == 0 and (level == 2 or level == 4):
		return True
	if 'outfile' in globals():
		global outfile
		file = open(outfile,'a')
		file.write(colored(prefix+message+"\n",collor))
		file.close()

	print colored(prefix+message,collor)
	if level == 1:
		exit(1)
if __name__ != "__main__":
	out('use this as a standalone script.',1)

if 	len(argv) < 2:
	print colored('''
....       :MM ..  M...  MM:............
........ M .......M.M....... M ........
......7M.........M...M.........M=......
  ...M... ....  M ....M......... M.....
  .=?.     . . M.  ... M..........Z7....
  N.... .  . .N.   .... D...........$...
 ,,..   .....D, ........,7..........?=.
 M...     ..:. ...........?..........M..
M.... .   ..N.............Z...........M
M ...     .$M....OMMMZ....MD..........M.
. .....   M.M. M ..... M..M.M ........+
  ...   .M..M,8.........7.M..M.........7
 .......M...MM........ . MM . M..  .   7
.......M....MN...........MM....M......+.
M.....M.....MM...........MM... .M ... M.
M ...M......M.M....... .Z M ..  .M    M
 M..M ......M. M ......M..M . ... M. M..
 ,.M .......M....~MMM:    M     . .M:I.
..O:..................    . .   .  .? ..
...++................. .  . .   . O$  .
.... M................ ..   ..  .M..  ..
......~M........... ..   .     M,  .  .
.........M............ .. . .M,..  .  ..
.......... .MM.......... MM... .. ... ..
     ....  .  .  .IZI...  . .  .   ..  .\n''', 'red')
	print '''
Shared domains enumerator script:

Usage: python '''+basename(argv[0])+''' domain [-tor, -f out.txt]
	-tor: enable tor support you need to enable the control service to work.
	-f:   output to file (if exist warning will be displayed)
'''
	exit()
def control_init():
	global sock
	sock = socket()
	sock.connect((tor_host,tor_control_port))
	sock.send("AUTHENTICATE\r\n")
	if 'OK' in sock.recv(10):
		return True
	else:
		raise Exception

def change_ip():
	global tor, tor_control_port, tor_host, sock
	if tor is True:
		if 'sock' not in globals():
			control_init()
		try:
			sock.send("SIGNAL NEWNYM\r\n")
			if 'OK' in sock.recv(10):
				return True
		except error:
			return False
	else:
		return False
def get_data(domain):
	global tor, tor_port, tor_host
	if tor is True:
		opener = Http(proxy_info = ProxyInfo(PROXY_TYPE_SOCKS4, tor_host, tor_port, True))
	else:
		opener = Http()
	data = urlencode({'key':'', 'remoteAddress':domain})
	code, content = opener.request('http://domains.yougetsignal.com/domains.php', 'POST', data, {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:29.0) Gecko/20100101 Firefox/29.0',
                                                                                             'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})
	del opener
	return code, content
def resolve_host(host):
	global tor, tor_host, tor_control_port, sock
	if tor is True:
		if 'sock' not in globals():
			control_init()
		try:
			sock.send("SETEVENTS ADDRMAP\r\n")
			if 'OK' in sock.recv(10):
				sock.send("RESOLVE %s\r\n" % host)
				while True:
					back = sock.recv(1024)
					if 'ADDRMAP '+host in back:
						if host+' <error>' in back:
							sock.send("SETEVENTS\r\n")
							if 'OK' not in sock.recv(1024):
								raise Exception
							raise gaierror
						reobj = compile(r"ADDRMAP ([^\s]+) ([0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3})", IGNORECASE)
						result = reobj.findall(back)
						if str(result[0][0]) == str(host):
							sock.send("SETEVENTS\r\n")
							if 'OK' not in sock.recv(1024):
								raise Exception
							return result[0][1]
		except gaierror:
			raise
		except error:
			raise
	else:
		return gethostbyname(host)

for index, data in enumerate(argv):
	system('cls' if name == 'nt' else 'clear')
	if not search(r"\b([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}\b", argv[1], IGNORECASE | VERBOSE):
		out('wrong syntax or domain used exiting...',1)
	if data == '-f' and len(argv) > index+1:
		if isfile(argv[index+1]):
			try:
				for i in range(0,10):
					stdout.write(colored('[-] Given output file exists you have '+str(int(10)-i)+' seconds. press delete or Ctrl-C to bypass...\r','red'))
					sleep(1)
					stdout.flush()
				out('time out exiting...',1)
			except KeyboardInterrupt:
				print colored("\n"+'[+] Bypass detected...','green')
				instruction = raw_input(colored('[?] are you sure you want to continue? [y/n]: ','green'))
				if instruction.lower() != 'y':
					out('desition taken exiting...',1)
				print colored('[+] Removing old file...','green')
				try:
					remove(argv[index+1])
					print colored('[+] File removed continuing...','green')
				except os_error:
					out('file not deleted exiting...',1)
				outfile = argv[index+1]
		else:
			outfile = argv[index+1]
	elif data == '-f' and len(argv) <= index+1:
		out('-f argument require a statement exiting...',1)
	if data == '-tor':
		tor = True
	elif data != '-tor' and 'tor' not in locals():
		tor = False

if  tor is True:
	try:
		code, returndata = Http(proxy_info = ProxyInfo(PROXY_TYPE_SOCKS4, tor_host, tor_port, True)).request('https://check.torproject.org/api/ip')
		if code.status == 200:
			tor_data = loads(returndata)
			if tor_data['IsTor'] is False:
				out('we are not using tor exiting...',1)
			else:
				out('tor check successful...',3)
		else:
			raise HttpLib2Error
	except HttpLib2Error:
		out('error in tor check routine exiting...',1)

domain = str(argv[1])
try:
	ip = resolve_host(domain)
except gaierror:
	out('main domain ip address cannot be resolved exiting...',1)

out('given domain ip obtained: '+str(ip),3)
cond = True
while cond:
	code, content = get_data(domain)
	if code.status != 200:
		out('wrong status code returned probably cloudflare is blocking our requests...',2)
		if change_ip() is True:
			out('we changed ip retrying...',2)
			sleep(2)
		else:
			out('ip change failed exiting...',1)

	if code.status == 200:
		correlated = loads(content)
		if 'fail' in correlated['status'].lower():
			if 'daily reverse' in correlated['message'].lower():
				if change_ip() is False:
					out('daily limit reached try change your ip address or use tor instead...',1)
				else:
					out('daily limit reached we changed ip retrying...',2)
					sleep(2)
			elif 'heavy load' in correlated['message'].lower():
				if change_ip() is False:
					out('maybe there on to us try change your ip address or use tor instead...',1)
				else:
					out('something is wrong maybe there on to us we have changed ip retrying...',2)
					sleep(2)
			else:
				out('unknown fail message: '+correlated['message'],1)

		elif 'success' in correlated['status'].lower() and len(correlated['domainArray']) >= 1:
			cond = False
			for x in correlated['domainArray']:
				try:
					domainip = resolve_host(x[0])
				except gaierror:
					fail = True
					pass
				if 'fail' in locals() and 'www.' not in x[0]:
					try:
						domainip = resolve_host('www.'+x[0])
						prefix = True
						del fail
					except gaierror:
						out('domain '+x[0]+' cannot be resolved.', 4)
						del fail
						continue
				elif 'fail' in locals() and 'www.' in x[0]:
					out('domain '+x[0]+' cannot be resolved.', 4)
					del fail
					continue
				if domainip in ip:
					if 'prefix' in locals():
						out('domain www.' + x[0] + ' found.', 3)
						del domainip
						del prefix
					else:
						out('domain ' + x[0] + ' found.', 3)
						del domainip
				elif domainip not in ip and 'www.' not in x[0]:
					out('www prefix for '+x[0]+' missing retrying...',2)
					try:
						domainip = resolve_host('www.'+x[0])
					except gaierror:
						del domainip
						out('domain '+x[0]+' with prefix cannot be resolved.',4)
						out('domain '+x[0]+' with/without prefix not bound to target ip.',2)
						continue
					if domainip in ip:
						out('domain www.' + x[0] + ' found.', 3)
						del domainip
					else:
						del domainip
						out('domain '+x[0]+' with/without prefix not bound to target ip.',2)
				else:
					del domainip
					out('domain '+x[0]+' not bound to target ip.',2)
		else:
			out('Unexpected behavior detected from remote system exiting...',1)
out(str(domain_counter),5)
if 'sock' in globals():
	sock.send("QUIT\r\n")
	sock.close()
