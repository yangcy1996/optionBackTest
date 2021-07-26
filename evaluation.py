# -*- coding: utf-8 -*-
"""
@author: Chengye
"""
import pandas as pd
import numpy as np

class Metrics():
    """
    Pnl metrics calculators
    """
    def calcSharpeRatio(pnls, periods=252):
        """
        Calculatee the Sharpe ratio based on daily pnls, 
        benchmark is zero (i.e. no risk-free rate information).
        
        Parameters:
        pnls -- A pandas Series representing daily pnl.
        periods -- number of periods in one year.
        
        Returns
        sharpe ratio
        """
        return np.sqrt(periods) * np.mean(pnls) / np.std(pnls)
    
    def calcDrawdowns(pnls):
        """
        Calculate the largest peak-to-trough drawdown of the pnl curve
        as well as the duration days of the longest drawdown. Requires that the
        pnls is a pandas Series.
        
        Parameters:
        pnls -- A pandas Series representing daily dollar pnls
        
        Returns:
        dd.min() -- max drawdown. 
        dd_duration.max() -- longest unprofitable period (days).
        """
        cumPnls = pnls.cumsum()
        dd = cumPnls - cumPnls.cummax()
        negative_dd = (dd < 0).astype(bool)
        sum_negative_dd = negative_dd.cumsum()
        dd_duration = (sum_negative_dd - sum_negative_dd.mask(
            negative_dd).ffill().fillna(0).astype(int))

        return dd.min(), dd_duration.max()
