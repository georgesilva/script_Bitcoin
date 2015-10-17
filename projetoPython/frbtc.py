#!/usr/bin/python
# -*- coding: utf-8 -*-
import signal, os
import mechanize, urllib2, cookielib
import random, re, time, math

mode = "lo"
clientSeed = "0"
csrf_token = "0"
maxWait = 500
stop = False
timeout = False
lossesCounter = 0
randNumber = '0.23360912990756333'
saldoInicial = 0
sumLosses = 0
sumWin = 0
maxLoss = 0
initTime = 0
iterator = 0
loseStats = [[] for k in range(200)]


def openBrowser(wallet, password):
	# Browser
	br = mechanize.Browser()

	# Cookie Jar
	cj = cookielib.LWPCookieJar()
	br.set_cookiejar(cj)

	# Browser options
	br.set_handle_equiv(True)
	br.set_handle_gzip(True)
	br.set_handle_redirect(True)
	br.set_handle_referer(True	)
	br.set_handle_robots(False)

	# Follows refresh 0 but not hangs on refresh > 0
	br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

	# Want debugging messages?
	br.set_debug_http(False)
	br.set_debug_redirects(False)
	br.set_debug_responses(False)

	# User-Agent (this is cheating, ok?)
	br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2522.1 Safari/537.36')]


	# Open some site
	response = br.open('http://freebitco.in/')


	#Doing the login
	br.select_form(nr=2)
	br['btc_address'] = wallet
	br['password'] = password
	response = br.submit()
	httpResult = response.read().split(":")

	#Setting cookies
	cookieBTCAddress = "btc_address="+httpResult[1]+"; expires=3650"
	cookiePassword = "password="+httpResult[2]+"; expires=3650"
	br.set_cookie(cookieBTCAddress)
	br.set_cookie(cookiePassword)
	br.set_cookie("sm_dapi_session=1; expires=3650")
	br.set_cookie("cookieconsent_dismissed=yes; expires=3650")
	br.set_cookie("have_account=1; expires=3650")

	#Loading the bet page
	response = br.open('http://freebitco.in/?op=home&tab=double_your_btc#')
	
	global csrf_token
	cookie = response.info()['Set-Cookie']
	if 'csrf_token' in cookie:
		init = cookie.find('=')
		end = cookie.find(';')
		csrf_token = cookie[init+1:end]

	return br




def makeBet(br, initBet, stopPercentage, odds, multiplier, imfe):
	"Funcao que faz a aposta utilizando os parametros. Retorna o balanço atualizado em BTCs."
	global iterator
	global saldoInicial
	global stop
	global sumLosses
	global lossesCounter
	global sumWin
	global maxLoss
	global csrf_token
	global clientSeed
	global randNumber

	bet = initBet
	initiate()
	clientSeed = getClientSeed(br)

	with GracefulInterruptHandler() as h:
		while True:
			iterator = iterator+1
			#SIGALRM is only usable on a unix platform
			signal.signal(signal.SIGALRM, timeoutHandler)
			#change 5 to however many seconds you need
			signal.alarm(25)
			try:
				response = br.open('http://freebitco.in/cgi-bin/bet.pl?m='+mode+'&client_seed='+clientSeed+'&jackpot=0&stake='+
									str("{:.8f}".format(bet))+'&multiplier='+odds+'&rand='+str(randNumber)+
									'&csrf_token='+csrf_token)
			except urllib2.URLError as e:
				print "Request Timed Out occurred. Waiting a few moments before trying again."
				time.sleep(2)
				continue
			except TimeExceededError:
				print "###### Request hanging. Waiting to refresh. #######"
				time.sleep(5)
				continue
			except:
				print "Erro louco."
				time.sleep(5)
				continue

			signal.alarm(0)
			serverResponse = response.read().split(':')
			
			if serverResponse[0] != 's1':
				print "An internal error occurred."
			elif serverResponse[0] == 'e2':
				print "Bet is too low."
			else:
				balance = serverResponse[3]
				if iterator == 1:
					saldoInicial = balance
				if iterator % 200 == 0:
					execTime = getExecTime()
					if execTime > 240:
						print "Mais de 4 horas trabalhando. Hora de descansar..."
						time.sleep(2700)
				if serverResponse[1] == 'w':
					sumWin = sumWin+1
					bet = reset(initBet)
					if stop ==  True:
						stop = False
						printStats(balance)
						return balance
					if lossesCounter > maxLoss:
						maxLoss = lossesCounter
					print ""
					print 'You WON! After losing ' + str(lossesCounter) + ' times. Restarting now!'
					print 'Your maximum number of consecutive losses is ' + str(maxLoss)
					if lossesCounter <= 200:
						loseStats[lossesCounter] = loseStats[lossesCounter]+1
					lossesCounter = 0
				elif serverResponse[1] == 'l':
					sumLosses = sumLosses+1
					lossesCounter = lossesCounter+1
					if lossesCounter > 0:
						bet = multiply(bet, imfe, multiplier)
					if iHaveEnoughMoni(bet, float(balance), stopPercentage) == False:
						print 'Your bet reached a maximum threshold. Reseting for your safety. ' + str(lossesCounter)
						print ""
						bet = reset(initBet)
						if lossesCounter > maxLoss:
							maxLoss = lossesCounter
						if lossesCounter <= 200:
							loseStats[lossesCounter] = loseStats[lossesCounter]+1
					print 'You LOST! Multiplying your bet and betting again.'
			getRandomWait()
			if h.interrupted:
				stop = True
				print "###############################################################################################"
				print "Voce apertou Ctrl-C. Saindo..."
	return balance

def getClientSeed(br):
	"Extrai next_client_seed da pagina"
	response = br.open('https://freebitco.in/?op=home&tab=double_your_btc#')
	br.form = br.global_form()
	seed = br.find_control(id="next_client_seed").value
	return seed

def getInitialBalance(br):
	""
	return saldoInicial


def getToken(br):
	"Extrai o token necessario para enviar como parametro a cada aposta"
	response = br.open('https://freebitco.in/?op=home&tab=double_your_btc#')
	cookie = response.info()['Set-Cookie']
	if 'csrf_token' in cookie:
		init = cookie.find('=')
		end = cookie.find(';')
		csrf_token = cookie[init+1:end]

def reset(initBet):
	return initBet

def multiply(bet, imfe, multiplier):
	"Aumenta as apostas dentro de um ciclo de perdas"
	multiplyTo = multiplier
	if (lossesCounter > 0 and lossesCounter <= 5 and imfe):
		multiplyTo = 1.20
	elif (lossesCounter > 54 and multiplyTo > 1.12):
		multiplyTo = multiplyTo - 0.01

	value = bet * multiplyTo
	return  value

def getRandomWait():
	"Faz com que os tempos entre uma aposta e outra seja aleatorio"
	wait = random.random() * maxWait
	wait = wait+100
	print 'Waiting for ' + str('{:.0f}'.format(wait)) + 'ms before next bet.', time.asctime( time.localtime(time.time()) )
	tempo = wait/1000
	time.sleep(tempo)
	return

def iHaveEnoughMoni(bet, balance, pctg):
	"Verifica se esta na hora de parar. Retorna true or false"
	return (balance * pctg) > bet

def initiate():
	global loseStats
	global initTime
	initTime = time.time()
	for i in range(0,200):
		loseStats[i] = 0

def getExecTime():
	"Retorna tempo de execucao em minutos"
	global initTime
	duration = (time.time() - initTime)/60
	return duration

def formatTime(duration):
	"Passa tempo para texto"
	twodigitsFormat = '{:.2f}'
	eightdigitsFormat = '{:.8f}'
	
	if duration < 120:
		minutos = twodigitsFormat.format(duration)
		tempoTxt = str(minutos) + ' minutes.'
	else:
		horas = duration/60
		horas = twodigitsFormat.format(horas)
		tempoTxt =  str(horas) + ' hours.'
	return tempoTxt


def printStats(balance):
	"Salva estatisticas em arquivo texto"
	#TODO por enquanto print on screen
	twodigitsFormat = '{:.2f}'
	eightdigitsFormat = '{:.8f}'
	sumTotal = sumWin + sumLosses
	pctWin = float(sumWin)/float(sumTotal)
	pctWin = pctWin*100
	pctLost = float(sumLosses)/float(sumTotal)
	pctLost = pctLost*100

	print 'Winings: ' + str(sumWin) + ' [' + str(twodigitsFormat.format(pctWin)) + '%]. Losses: ' + str(sumLosses) + ' [' + str(twodigitsFormat.format(pctLost)) + '%]. Total: ' + str(sumTotal)
	
	strTempo = formatTime(getExecTime())

	profit = eightdigitsFormat.format(float(balance) - float(saldoInicial))
	
	print 'You Won ' + str(profit) + ' BTCs.'
	print 'Your actual balance is: ' + str(balance) + ' BTCs. Running for ' + strTempo
	for i in range(0, 200):
		if loseStats[i] != 0:
			print str(i) + ' => ' + str(loseStats[i]) + ' times.'

def timeoutHandler(signum, frame):
	print "sig alarm"
	raise TimeExceededError


###############ANOTATIONS
#$.get('/cgi-bin/bet.pl?m='+mode+'&client_seed='+client_seed+'&jackpot='+jackpot+'&stake='+bet+'&
#		multiplier='+$( "#double_your_doge_payout_multiplier" ).val()+'&rand='+Math.random(),

#httpResult[0] = success or fail
#httpResult[1] = "w" or "l" 
#httpResult[2] = bet random number
#httpResult[3] = new Balance
#httpResult[6] = new seed hash of server
#httpResult[8] = new NONCE
#httpResult[9] = old seed of server
#httpResult[10] = old seed hash of server
#httpResult[11] = old seed of client
#httpResult[12] = old NONCE
#httpResult[16] = is the maximum you can bet



#Gerenciador de sinal de parada
class TimeExceededError():
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class GracefulInterruptHandler(object):

    def __init__(self, sig=signal.SIGINT):
        self.sig = sig

    def __enter__(self):

        self.interrupted = False
        self.released = False

        self.original_handler = signal.getsignal(self.sig)

        def handler(signum, frame):
            self.release()
            self.interrupted = True

        signal.signal(self.sig, handler)

        return self

    def __exit__(self, type, value, tb):
        self.release()

    def release(self):

        if self.released:
            return False

        signal.signal(self.sig, self.original_handler)

        self.released = True

        return True
	
