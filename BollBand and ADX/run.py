import backtrader as bt
import pandas as pd
import os,sys,argparse
import datetime
import csv
import math
from BB_ADX import BBADX

if __name__ == '__main__':
    # Create optimization.csv file for optstrategy logging
    fields = ['BB_MA', 'BB_SD', 'ADX_Period', 'End Value']
    with open('optimization.csv', 'w') as csvfile:  
        csvwriter = csv.writer(csvfile)  
        csvwriter.writerow(fields)

    cerebro = bt.Cerebro()

    eurusd_prices = pd.read_csv('mid_data_4000_H1.csv', parse_dates=True, index_col='Time')

    feed = bt.feeds.PandasData(dataname=eurusd_prices, timeframe=bt.TimeFrame.Minutes, compression=60)
    cerebro.adddata(feed)

    # cerebro.optstrategy(BBADX, BB_SD=[], BB_MA=range(), ADX_Period=range())
    cerebro.addstrategy(BBADX)

    cerebro.broker.setcash(50000.0)

    cerebro.broker.setcommission(commission=.0000)

    cerebro.addsizer(bt.sizers.FixedSize, stake=10000)

    # Multiply by sqrt(24*252) for H1 candles
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0, timeframe=bt.TimeFrame.Minutes, compression=60)
    
    # cerebro.addanalyzer(BasicTradeStats)

    strategy = cerebro.run()    
    for each in strategy[0].analyzers:
        each.print()

    cerebro.plot(style='candlestick')
