# -*- coding: utf-8 -*-
"""
@author: Chengye
"""

import os
import pandas as pd
import logging
from datetime import datetime
from base import Trade
from base import Option
from portfolio import Portfolio
from evaluation import Metrics

'''
PNL Metrics Definition:
1.	Daily trade P&L: Time series, sum of P&L of all the new option trades, from trade time to today’s close.
2.	Daily position P&L: Time series, sum of P&L of all existed positions from previous COB to current COB. 
    Existed position is defined as the option, stock and cash positions on previous COB. 
3.	Daily total P&L: Time series, sum of daily trade P&L and daily position P&L.
4.	Cumulative total P&L for the entire date range: Time series, cumulative sum of daily total P&L.
5.	Total P&L/contract: considered a mini delta-hedged portfolio for each option symbol, 
    calculate the approximate total P&L of each mini portfolio, assuming no funding cost. 
6.	Longest unprofitable period: the longest consecutive days in which cumulative P&L is below previous highest cumulative P&L.
7.	Max peak to trough drawdown: maximum drawdown in USD.
8.	Annualized sharpe ratio: (avg daily PL*sqrt (252))/sd of daily pl
'''

class BackTest(object):
    ''' 
    Class for running a backtest session
    
    Inputs:
        optionData -- dataFrame of all options information
        tradeData -- dataFrame of all trade information
        vegaLimit -- vega limit on stock and portfolio
        ir -- overnight interest rate, assume it's constant
        cost -- option transaction cost ratio
                assume it's constant for both options and stock trading
                accounts for slippage, commission fee, finance cost, etc
                assume no transaction cost for option expire and stock rebalance   
    '''
    def __init__(self, optionData, tradeData, vegaLimit, ir, cost=0):
        # Input
        self.optionData = optionData
        self.tradeData = tradeData
        self.vegaLimit = vegaLimit
        self.ir = ir
        self.cost = cost
        
        # date range list
        self.dateList = list(set(optionData['DataDate']))
        self.dateList.sort()
        # underlying ticker list
        self.stockList = list(set(optionData['UnderlyingSymbol']))
                
    def loadTrades(self, date):
        '''
        Store all the trades for a certain date and sort them by trade time

        Parameters: 
        date -- datetime

        Returns:
        tradeList -- list of Trade objects, in trade time ascending order
        '''
        tempTradeData = self.tradeData.loc[self.tradeData['Date'] == date].sort_values('Time')
        tradeList = []
        for index, row in tempTradeData.iterrows():
            tradeList.append(Trade(row['Date'], row['Time'], row['OptionSymbol'], 
                                   row['Price'], row['Vega'], row['Quantity']))
        return tradeList
    
    def loadOptions(self, date):
        '''
        Store all the option information for a certain date

        Parameters:
        date -- datetime

        Returns:
        optionDict -- dictionary of Option objects
        '''
        optionDict={}
        tempOptionData = self.optionData.loc[self.optionData['DataDate'] == date]
        for index, row in tempOptionData.iterrows():
            option = Option(row['DataDate'], 
                            row['UnderlyingSymbol'], 
                            row['OptionSymbol'], 
                            row['Delta'], 
                            row['UnderlyingPrice'], 
                            row['Signal'], 
                            row['Multiplier'], 
                            row['Vega'], 
                            row['Last'])
            optionDict[row['OptionSymbol']] = option
        return optionDict                           
        
    def run(self, agreeType):
        '''
        Run backtest

        Parameters:
        agreeType -- bool, true if portfolio trades agree with previous day's signal, 
                     false otherwise

        Returns:
        dailyPnls -- dataframe that contains daily trade pnl, daily position pnl, 
                     daily total pnl and cumulative total pnl for each day
        contractTotPnl -- dictionary of doubles, total pnl of each option symbol
        '''
        
        portfolioPnls = pd.DataFrame(0, index = self.dateList, 
                                      columns = ['DailyTradePnl', 
                                                 'DailyPositionPnl', 
                                                 'DailyTotPnl',
                                                 'CumTotPnl'])        
        date = self.dateList[0]
        optionDict = self.loadOptions(date)          
        pf = Portfolio(agreeType, self.vegaLimit, self.stockList, optionDict, 
                       date, self.ir, self.cost)
        for date in self.dateList[1:]:
            logging.info('BtDate = ' + str(date)[:11])
            tradeList = self.loadTrades(date)
            if len(tradeList)==0:
                continue
            # handle each trade one by one, in ascending tradetime 
            for trade in tradeList:
                pf.handleTrade(trade) 
            # update option info at COB, calculate daily pnls and rehedge
            optionDictNew = self.loadOptions(date)
            pf.updateEOD(optionDictNew, date)
            # store daily pnls
            portfolioPnls.loc[date] = [pf.dailyTradePnl, 
                                       pf.dailyPositionPnl, 
                                       pf.dailyTotPnl,
                                       pf.totPnl]
        contractTotPnl = pf.contractTotPnl
        return portfolioPnls, contractTotPnl
    
def readData(optionFileName, tradeFileName):
    '''
    Read csv files for option and trade, sotre into pandas dataframe
    '''
    optionData = pd.read_csv(optionFileName)
    optionData['DataDate'] = pd.to_datetime(optionData['DataDate'])
    
    tradeData = pd.read_csv(tradeFileName)
    tradeData['Date'] = pd.to_datetime(tradeData['Date'])
    tradeData['Time'] = [datetime.strptime(x, '%H:%M:%S').time() for x in tradeData['Time']]
    
    return optionData, tradeData

def saveToCsv(portfolioPnls, contractTotPnl, maxDrawdown, longestUnprofit, 
               sharpeRatio, savePath, agreeType):
    '''
    save all pnl metrics to csv files
    '''
    portfolioPnls.to_csv(os.path.join(savePath, "portfolio_pnls_%r.csv"%agreeType))
    pd.DataFrame.from_dict(data=contractTotPnl, orient='index').to_csv(
            os.path.join(savePath, "contract_total_pnls_%r.csv"%agreeType), header=['totalPnls'])
    metrics = pd.Series([maxDrawdown, longestUnprofit, sharpeRatio], 
                        index = ['maxDrawDown','longestUnprofitDays', 'sharpeRatio'])
    metrics.to_csv(os.path.join(savePath, "other_metrics_%r.csv"%agreeType), header=['values'])
    
if __name__ == '__main__':
    path = os.path.abspath(os.path.join(__file__, '..'))
    optionFileName = os.path.join(path, "option_sample.csv")
    tradeFileName = os.path.join(path, "trade_sample.csv")
    
    optionData, tradeData = readData(optionFileName, tradeFileName)
    vegaLimit = 5000
    ir = 0.015
    cost = 0.005
    bt = BackTest(optionData, tradeData, vegaLimit, ir, cost)

    resultDict = {True:{}, False:{}} # result dictionary for both portfolios
    for agreeType in [True, False]:
        logging.info("Backtesting for agreeType = %r" %agreeType)
        portfolioPnls, contractTotPnl = bt.run(agreeType)
        maxDrawdown, longestUnprofit = Metrics.calcDrawdowns(portfolioPnls['DailyTotPnl'])
        sharpeRatio = Metrics.calcSharpeRatio(portfolioPnls['DailyTotPnl'])
        result = {'DailyTradePnl': portfolioPnls['DailyTradePnl'],
                  'DailyPositionPnl': portfolioPnls['DailyPositionPnl'],
                  'DailyTotalPnl': portfolioPnls['DailyTotPnl'],
                  'CumTotalPnl': portfolioPnls['CumTotPnl'],
                  'ContractTotalPnl': contractTotPnl,
                  'longestUnprofitDays': longestUnprofit,
                  'MaxDrawdown': maxDrawdown,
                  'SharpeRatio': sharpeRatio}
        resultDict[agreeType] = result
        saveToCsv(portfolioPnls, contractTotPnl, maxDrawdown, longestUnprofit, 
               sharpeRatio, path, agreeType)
        
    