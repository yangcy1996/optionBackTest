# -*- coding: utf-8 -*-
"""
@author: Chengye
"""

import pandas as pd
import logging

class Portfolio(object):
    ''' Class for a portfolio
    Portfolio inputs:
        agreeType -- agree or disagree with previous day's signal
        vegaLimit -- vega limit on stock and portfolio
        stockList -- a list of all underlying tickers
        optionDict -- a dictionary of all options in the option data file
        today -- current date of the portfolio
        ir -- overnight interest rate, assume it's constant
        cost -- option transaction cost ratio
    '''
    def __init__(self, agreeType, vegaLimit, stockList, optionDict, today, 
                 ir, cost):
        # Input
        self.agreeType = agreeType
        self.vegaLimit = vegaLimit
        self.stockList = stockList
        self.optionDict = optionDict
        self.optionSymbolList = list(set(self.optionDict.keys()))
        self.today = today
        self.ir = ir
        self.cost = cost
        
        # Portfolio total metrics
        self.dailyTradePnl = 0
        self.dailyPositionPnl = 0
        self.dailyTotPnl = 0
        self.totPnl = 0
        self.totVega = 0
        self.totCash = 0
        
        # Metrics per option contract
        self.contractTotPnl = {}
        
        # Metrics per stock name
        self.stockDelta = pd.Series(0, index = stockList)
        self.stockVega = pd.Series(0, index = stockList)
        
        # Portfolio positions
        self.stockPosition = pd.Series(0, index = stockList)
        self.optionPosition = {}
        self.newDailyTrade = []
    
    def handleTrade(self, trade):
        '''
        Handle a new trade, add the trade to newDailyTrade if all conditions met
        
        Parameters:
        trade -- Trade object
        '''
        tradeVega = trade.getTradeVega()
        tradeSymbol = trade.getOptionSymbol()
        quantity = trade.getQuantity()
        logging.info('Check trade '+tradeSymbol)
        if tradeSymbol not in self.optionDict:
            logging.info("tradeSymbol not appear in the past")
            return
        
        option = self.optionDict[tradeSymbol]
        underlyer = option.getUnderlyingTicker()
        
        # check if this trade matches the agree type of this portfolio
        if (quantity * option.getSignal()>0)!=self.agreeType:
            logging.info("Agree type not match")
            return
        
        # check if meet the risk limits
        # assume vega of existing positions didn't change from
        # previous close values
        thisVega = quantity * tradeVega * option.getContractMultiplier()
        if abs(self.totVega + thisVega) > self.vegaLimit:
            logging.info("Breach total vega")
            return
        if abs(self.stockVega.loc[underlyer] + thisVega) > self.vegaLimit:
            logging.info("Breach stock vega")
            return
        
        # accept the trade and update
        self.totVega += thisVega
        self.stockVega[underlyer] += thisVega
        self.newDailyTrade.append(trade)
        
    def calcDailyTradePnl(self, optionDictNew):
        '''
        Calculate the sum of daily trade pnl of all the new accepted trades
        Also update option positions of new trades
        This function should be used after calcDailyPositionPnl to avoid double-count

        Parameters:
        optionDictNew : dictionary of option objects
        '''
        logging.info("Calculating daily trade Pnl")
        self.dailyTradePnl = 0
        for trade in self.newDailyTrade:
            optionSymbol = trade.getOptionSymbol()
            logging.info('Calculating trade '+optionSymbol)
            if optionSymbol not in optionDictNew:
                logging.warning("Can't find trade's option in optionDictNew")
                continue
            option = optionDictNew[optionSymbol]
            quantity = trade.getQuantity()
            multiplier = option.getContractMultiplier()
            if quantity>0:
                tradePrice = trade.getTradePrice() * (1 + self.cost)
            else:
                tradePrice = trade.getTradePrice() * (1 - self.cost)    
            cashChange = -tradePrice * quantity * multiplier
            tradePnl = (option.getOptionPrice() - tradePrice) * quantity * multiplier
            
            # update pnls
            self.dailyTradePnl += tradePnl
            if optionSymbol in self.contractTotPnl:
                self.contractTotPnl[optionSymbol] += tradePnl
            else:
                self.contractTotPnl[optionSymbol] = tradePnl
            
            # update positions
            self.totCash += cashChange
            if optionSymbol in self.optionPosition:
                self.optionPosition[optionSymbol] += quantity
            else:
                self.optionPosition[optionSymbol] = quantity
        # reset new daily trade list
        self.newDailyTrade = []
    
    def calcDailyPositionPnl(self, optionDictNew, date):
        '''
        calculate daily position pnl
        positionPnl = optionPositionPnl + stockPositionPnl + cashPnl
        also aggregate contract total pnl
        contractTotPnl += optionContractPositionPnl
        also check if option position has expired, 
        if expired, move option position value to cash

        Parameters:
        optionDictNew -- dictionary of Option objects, option information of that date
        date -- datetime, the date to calculate daily position pnl.
        '''
        logging.info("Calculating daily position Pnl")
        self.dailyPositionPnl = 0
        # Calculate cash pnl, positive if totCash>0, negative if totCash<0
        days = (date - self.today).days
        cashPnl = self.totCash * self.ir * days / 360
        self.dailyPositionPnl += cashPnl
        # Calculate position pnl for each contract
        tempPosition = self.optionPosition.copy()
        for optionSymbol in tempPosition:
            if optionSymbol in optionDictNew:
                # optionSymbol still in today's optionDict,
                # meaning it's not expired, calculate pnl
                position = tempPosition[optionSymbol]
                optionPre = self.optionDict[optionSymbol]
                optionNow = optionDictNew[optionSymbol]
                multiplier = optionPre.getContractMultiplier()
                delta = optionPre.getDelta()
                optionPriceChange = optionNow.getOptionPrice() - optionPre.getOptionPrice()
                spotPriceChange = optionNow.getSpot() - optionPre.getSpot()
                optionPnl = position * multiplier * optionPriceChange
                stockPnl = -position * multiplier * delta * spotPriceChange
                self.contractTotPnl[optionSymbol] += optionPnl + stockPnl
                self.dailyPositionPnl += optionPnl + stockPnl
            else:
                # option expired, no actual pnl
                position = tempPosition[optionSymbol]
                optionPre = self.optionDict[optionSymbol]
                multiplier = optionPre.getContractMultiplier()
                delta = optionPre.getDelta()
                if delta!=0:
                    logging.warning("An option expired with delta not equals 0")
                # update cash positon
                self.totCash += position * multiplier * optionPre.getOptionPrice()
                # remove option position
                del self.optionPosition[optionSymbol]
    
    def updateGreeksAndRehedge(self):
        '''
        update all Greeks before rehedging
        calculate portfolio vega, stock vega and remaining stock delta
        if remaining delta is not 0, rehedge stock positons
        '''
        self.totVega = 0
        self.stockDelta = pd.Series(0, index = self.stockList)
        self.stockVega = pd.Series(0, index = self.stockList)
        stockSpot = pd.Series(0, index = self.stockList)
        for optionSymbol in self.optionPosition:
            position = self.optionPosition[optionSymbol]
            option = self.optionDict[optionSymbol]
            underlyingTicker = option.getUnderlyingTicker()
            stockSpot.loc[underlyingTicker] = option.getSpot()
            multiplier = option.getContractMultiplier()
            delta = option.getDelta() * position * multiplier
            vega = option.getVega() * position * multiplier
            self.stockVega.loc[underlyingTicker] += vega
            self.stockDelta.loc[underlyingTicker] += delta
            self.totVega += vega
        for stock in self.stockList:
            self.stockDelta.loc[stock] += self.stockPosition.loc[stock]
            remainingDelta = self.stockDelta.loc[stock]
            if remainingDelta != 0:
                # has remaining delta, 
                # need to sell remaining delta amount of stock
                self.stockPosition.loc[stock] += -remainingDelta
                self.totCash += remainingDelta * stockSpot.loc[stock]
                self.stockDelta.loc[stock] = 0
                
    def updateEOD(self, optionDictNew, date):
        '''
        Update at the end of date, using the steps below:
        1. calculate daily position pnl
        2. calculate daily trade pnl
        3. update total pnls
        4. update option information
        5. update Greeks and rehedge 
        
        Parameters:
        optionDictNew -- dictionary of Option objects, option info for that date
        date -- datetime, representing the date needs to update
        '''
        # 1. calculate daily position pnl 
        self.calcDailyPositionPnl(optionDictNew, date)
        # 2. calculate daily trade pnl
        self.calcDailyTradePnl(optionDictNew)
        # 3. update total pnls
        self.dailyTotPnl = self.dailyPositionPnl + self.dailyTradePnl
        self.totPnl += self.dailyTotPnl
        # 4. update option info from previous day to today's date
        self.optionDict = optionDictNew
        # 5. update Greeks and rehdge
        self.updateGreeksAndRehedge()
        # all updates are done, set today to date
        self.today = date