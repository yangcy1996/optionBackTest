# -*- coding: utf-8 -*-
"""
@author: Chengye
"""

class Option(object):
    ''' Class for an option'''
    def __init__(self, optionDate, underlyingTicker, optionSymbol, delta,
                 spot, signal, contractMultiplier, vega, optionPrice):
        self.__optionDate = optionDate
        self.__underlyingTicker = underlyingTicker
        self.__optionSymbol = optionSymbol
        self.__delta = delta
        self.__spot = spot
        self.__signal = signal
        self.__contractMultiplier = contractMultiplier
        self.__vega = vega
        self.__optionPrice = optionPrice
        
    def getOptionDate(self):
        return self.__optionDate
    
    def getUnderlyingTicker(self):
        return self.__underlyingTicker
    
    def getOptionSymbol(self):
        return self.__optionSymbol
    
    def getDelta(self):
        return self.__delta
    
    def getSpot(self):
        return self.__spot
    
    def getSignal(self):
        return self.__signal
    
    def getContractMultiplier(self):
        return self.__contractMultiplier
    
    def getVega(self):
        return self.__vega
    
    def getOptionPrice(self):
        return self.__optionPrice
    
    def setOptionDate(self, optionDate):
        self.__optionDate = optionDate
    
    def setUnderlyingTicker(self, underlyingTicker):
        self.__underlyingTicker = underlyingTicker
    
    def setOptionSymbol(self, optionSymbol):
        self.__optionSymbol = optionSymbol
    
    def setSpot(self, spot):
        self.__spot = spot
    
    def setSignal(self, signal):
        self.__signal = signal
    
    def setContractMultiplier(self, contractMultiplier):
        self.__contractMultiplier = contractMultiplier
    
    def setVega(self, vega):
        self.__vega = vega
    
    def setOptionPrice(self, optionPrice):
        self.__optionPrice = optionPrice


class Trade(object):
    ''' Class for a trade'''
    def __init__(self, tradeDate, tradeTime, optionSymbol, tradePrice, tradeVega, quantity):
        self.__tradeDate = tradeDate
        self.__tradeTime = tradeTime
        self.__optionSymbol = optionSymbol
        self.__tradePrice = tradePrice
        self.__tradeVega = tradeVega
        self.__quantity = quantity
        
    def getTradeDate(self):
        return self.__tradeDate
    
    def getTradeTime(self):
        return self.__tradeTime
    
    def getOptionSymbol(self):
        return self.__optionSymbol
    
    def getTradePrice(self):
        return self.__tradePrice
    
    def getTradeVega(self):
        return self.__tradeVega
    
    def getQuantity(self):
        return self.__quantity
    
    def setTradeDate(self, tradeDate):
        self.__tradeDate = tradeDate
        
    def setTradeTime(self, tradeTime):
        self.__tradeTime = tradeTime
        
    def setOptionSymbol(self, optionSymbol):
        self.__optionSymbol = optionSymbol
        
    def setTradePrice(self, tradePrice):
        self.__tradePrice = tradePrice
        
    def setTradeVega(self, tradeVega):
        self.__tradeVega = tradeVega
        
    def setQuantity(self, quantity):
        self.__quantity = quantity        
