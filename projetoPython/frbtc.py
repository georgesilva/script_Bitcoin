#!/usr/bin/python
# -*- coding: utf-8 -*-
import mechanize
import urllib
import cookielib
import random
import re
import time
import math

mode = "lo"
clientSeed = "0"
csrf_token = "0"
maxWait = 300
stop = False
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
	response = br.open('https://freebitco.in/')


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
	response = br.open('https://freebitco.in/?op=home&tab=double_your_btc#')
	
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
			response = br.open('/cgi-bin/bet.pl?m='+mode+'&client_seed='+clientSeed+'&jackpot=0&stake='+str("{:.8f}".format(bet))+
								'&multiplier='+odds+'&rand='+str(randNumber)+'&csrf_token='+csrf_token)
			serverResponse = response.read().split(':')
			balance = serverResponse[3]
			if iterator == 1:
				saldoInicial = balance
			if iterator % 200 == 0:
				printStats(balance)

			if serverResponse[0] != 's1':
				print "An error occurred"
			elif serverResponse[1] == 'w':
				sumWin = sumWin+1
				bet = reset(initBet)
				if stop ==  True:
					stop = False
					printStats(balance)
					return balance
				if lossesCounter > maxLoss:
					maxLoss = lossesCounter

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
					bet = reset(initBet)
					if lossesCounter > maxLoss:
						maxLoss = lossesCounter
					print 'Your bet reached a maximum threshold. Reseting for your safety. ' + str(lossesCounter)
					if lossesCounter <= 200:
						loseStats[lossesCounter] = loseStats[lossesCounter]+1
					lossesCounter = 0
				print 'You LOST! Multiplying your bet and betting again.'
			getRandomWait()
			if h.interrupted:
				stop = True
				print "###############################################################################################"
				print "Voce apertou Ctrl C. Saindo..."
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
    if (lossesCounter > 0 and lossesCounter <= 5 and imfe):
            multiplyTo = 1.20
    elif (lossesCounter > 5):
            multiplyTo = multiplier
    elif (lossesCounter > 54 and multiplyTo > 1.12):
            multiplyTo = multiplyTo - 0.01

    value = bet * multiplyTo
    return  value

def getRandomWait():
	"Faz com que os tempos entre uma aposta e outra seja aleatorio"
	wait = random.random() * maxWait
	print 'Waiting for ' + str('{:.0f}'.format(wait)) + 'ms before next bet.'
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
	
	tempo = (time.time() - initTime)/60
	if tempo < 240:
		tempo = twodigitsFormat.format(tempo)
		strTempo = str(tempo) + ' minutes.'
	else:
		tempo = tempo / 60
		tempo = twodigitsFormat.format(tempo)
		strTempo =  str(tempo) + ' hours.'

	profit = eightdigitsFormat.format(float(balance) - float(saldoInicial))
	
	print 'You Won ' + str(profit) + ' BTCs.'
	print 'Your actual balance is: ' + str(balance) + ' BTCs. Running for ' + strTempo
	for i in range(0, 200):
		if loseStats[i] != 0:
			print str(i) + ' => ' + str(loseStats[i]) + ' times.'




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
import signal

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
	
