# optionBackTest
Given a file of option information and a trade file, calculate the performance of two portfolios: one contains all trades that agree with the signal of previous day’s close, the other contains all trades that disagree. 

# Library Overview:
The library is designed in a modular way.

base.py – contains the two base classes, Option and Trade.

portfolio.py – contains the Portfolio class. Update daily. Manage all new trades during the day and open new positions if all limits have been met. Calculate basic risk metrics at the end-of-day and rehedge positions.

evaluation.py – contains the Metrics class, which hold several pnl metrics calculators. For now it contains calcSharpeRatio() for calculating annualized sharpe ratio and calcDrawdowns() for calculating max drawdown and longest recover period.

backTester.py – contains the BackTest class and the main function for this library. It sets up all parameters for a backtest, run the backtest and output the PnL metrics to result files. To run a backtest session, just put all files under the same directory and run backTester.py.

# Assumptions:

- No transaction cost for stock trading

- Transaction cost for option trading is a constant ratio

- Interest rate / funding rate are constant

- When checking vega limit at the time of a new trade, assume current vega of existing positions equals to their latest vega
