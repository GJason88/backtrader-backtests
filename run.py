import backtrader as bt
import pandas as pd
import os,sys,argparse
import datetime
import numpy as np # for optstrategy stop_pips, use linspace()
from Stochastic_SR_Backtest import StochasticSR

if __name__ == '__main__':
    '''Main method for StochasticSR Strategy'''
    cerebro = bt.Cerebro()

    # CSV data from my data-getter application: https://github.com/GJason88/oanda-data-getter 
    eurusd_prices = pd.read_csv('mid_data_test.csv', parse_dates=True, index_col='Time')

    # Data feed with compression of 60 minutes because mid_data_test.csv contains hourly candlestick data
    feed = bt.feeds.PandasData(dataname=eurusd_prices, timeframe=bt.TimeFrame.Minutes, compression=60)
    cerebro.adddata(feed)

    ## optstrategy for strategy optimization, addstrategy to test current strategy parameters
    # cerebro.optstrategy(StochasticSR, period=range(3,25))
    cerebro.addstrategy(StochasticSR)

    cerebro.broker.setcash(50000.0)

    cerebro.broker.setcommission(commission=0)

    cerebro.addsizer(bt.sizers.FixedSize, stake=10000)

    ## Sharpe Ratio analyzer example, not too applicable without some adjustments
    # cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0, timeframe=bt.TimeFrame.Minutes, compression=60)
    
    strategy = cerebro.run()    
    # print('Sharpe Ratio:', strategy[0].analyzers.sharpe.get_analysis())
    cerebro.plot()
