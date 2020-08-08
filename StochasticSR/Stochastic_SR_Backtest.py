import backtrader as bt
import logging
import datetime
import os.path
import sys

class StochasticSR(bt.Strategy):
    '''Trading strategy that utilizes the Stochastic Oscillator indicator for oversold/overbought entry points, 
    and previous support/resistance via Donchian Channels as well as a max loss in pips for risk levels.'''
    # parameters for Stochastic Oscillator and max loss in pips
    # Donchian Channels to determine previous support/resistance levels will use the given period as well
    # http://www.ta-guru.com/Book/TechnicalAnalysis/TechnicalIndicators/Stochastic.php5 for Stochastic Oscillator formula and description
    params = (('period', 14), ('pfast', 3), ('pslow', 3), ('upperLimit', 80), ('lowerLimit', 20), ('stop_pips', .002))

    def __init__(self):
        '''Initializes logger and variables required for the strategy implementation.'''
        # initialize logger for log function (set to critical to prevent any unwanted autologs, not using log objects because only care about logging one thing)
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        logging.basicConfig(format='%(message)s', level=logging.CRITICAL, handlers=[
            logging.FileHandler("LOG.log"),
            logging.StreamHandler()
            ])

        self.order = None
        self.donchian_stop_price = None
        self.price = None
        self.stop_price = None
        self.stop_donchian = None

        self.stochastic = bt.indicators.Stochastic(self.data, period=self.params.period, period_dfast=self.params.pfast, period_dslow=self.params.pslow, 
        upperband=self.params.upperLimit, lowerband=self.params.lowerLimit)

    def log(self, txt, doprint=True):
        '''logs the pricing, orders, pnl, time/date, etc for each trade made in this strategy to a LOG.log file as well as to the terminal.'''
        date = self.data.datetime.date(0)
        time = self.data.datetime.time(0)
        if (doprint):
            logging.critical(str(date) + ' ' + str(time) + ' -- ' + txt)


    def notify_trade(self, trade):
        '''Run on every next iteration, logs the P/L with and without commission whenever a trade is closed.'''
        if trade.isclosed:
            self.log('CLOSE -- P/L gross: {}  net: {}'.format(trade.pnl, trade.pnlcomm))


    def notify_order(self, order):
        '''Run on every next iteration, logs the order execution status whenever an order is filled or rejected, 
        setting the order parameter back to None if the order is filled or cancelled to denote that there are no more pending orders.'''
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status == order.Completed:
            if order.isbuy():
                self.log('BUY -- units: 10000  price: {}  value: {}  comm: {}'.format(order.executed.price, order.executed.value, order.executed.comm))
                self.price = order.executed.price
                # stop loss order for max loss of self.params.stop_pips pips
                self.stop_price = self.close(exectype=bt.Order.StopLimit, price=order.executed.price-self.params.stop_pips, oco=self.stop_donchian)
                # stop loss order for donchian SR price level
                self.stop_donchian = self.close(exectype=bt.Order.StopLimit, price=self.donchian_stop_price, oco=self.stop_price)
            elif order.issell():
                self.log('SELL -- units: 10000  price: {}  value: {}  comm: {}'.format(order.executed.price, order.executed.value, order.executed.comm))
                self.price = order.executed.price
                # stop loss order for max loss of self.params.stop_pips pips
                self.stop_price = self.close(exectype=bt.Order.StopLimit, price=order.executed.price+self.params.stop_pips, oco=self.stop_donchian)
                # stop loss order for donchian SR price level
                self.stop_donchian = self.close(exectype=bt.Order.StopLimit, price=self.donchian_stop_price, oco=self.stop_price)
        elif order.status in [order.Rejected, order.Margin]:
            self.log('Order rejected/margin')
        
        self.order = None


    def stop(self):
        '''At the end of the strategy backtest, logs the ending value of the portfolio as well as one or multiple parameter values for strategy optimization purposes.'''
        self.log('(period {}) Ending Value: {}'.format(self.params.period, self.broker.getvalue()), doprint=True)


    def next(self):
        '''Checks to see if Stochastic Oscillator, position, and order conditions meet the entry or exit conditions for the execution of buy and sell orders.'''
        if self.order:
            # if there is a pending order, don't do anything
            return
        if self.position.size == 0:
            # When stochastic crosses back below 80, enter short position.
            if self.stochastic.lines.percD[-1] >= 80 and self.stochastic.lines.percD[0] <= 80:
                # stop price at last support level in self.params.period periods
                self.donchian_stop_price = max(self.data.high.get(size=self.params.period))
                self.order = self.sell()
            # when stochastic crosses back above 20, enter long position.
            elif self.stochastic.lines.percD[-1] <= 20 and self.stochastic.lines.percD[0] >= 20:
                # stop price at last resistance level in self.params.period periods
                self.donchian_stop_price = min(self.data.low.get(size=self.params.period))
                self.order = self.buy() 
  
        if self.position.size > 0:
            # When stochastic is above 70, close out of long position
            if (self.stochastic.lines.percD[0] >= 70):
                self.close(oco=self.stop_price)
        if self.position.size < 0:
            # When stochastic is below 30, close out of short position
            if (self.stochastic.lines.percD[0] <= 30):
                self.close(oco=self.stop_price)
    
