#!/usr/bin/python
# -*- coding: utf-8 -*-
import frbtclib

wallet = 'ENDEREÇO DA SUA CARTEIRA BITCOIN'
password = 'SENHA'
startBet = 0.00000005 # Your balance must be 10^4 or 10^5 higher than this number. At least.
stopPercentage = 0.03  # Reaching this percentage of your balance the script stops. If you dont want it, put "2". Recommended "0.08" or lower. 
odds = '10'  # Your Payout
lossMulti = 1.14  # On Loss Multiply to (1.14 is equal to "Increase in 14%")
imfe = True # Decide if you want to increase your bet in 20% untill the 10th play on a lose cicle


browser = frbtclib.openBrowser(wallet, password)

currentBalance = frbtclib.makeBet(browser, startBet, stopPercentage, odds, lossMulti, imfe)

print "Exiting... Bye!"
