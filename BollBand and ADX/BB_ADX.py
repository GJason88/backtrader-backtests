import backtrader as bt
import pandas as pd
import csv

class BBADX(bt.Strategy):
    '''Mean Reversion trading strategy that utilizes Bollinger Bands for signals and ADX for locating and avoiding trends'''

    # Parameters that can be optimized for best performance for different markets or candlestick timeframes
    params = (('BB_MA', 20), ('BB_SD', 2), ('ADX_Period', 14), ('ADX_Max', 40))

    def __init__(self):
        '''Initializes all variables to be used in this strategy'''
        self.order = None
        self.stopprice = None
        self.closepos = None
        self.adx = bt.indicators.AverageDirectionalMovementIndex(self.data, period=self.params.ADX_Period)
        self.bb = bt.indicators.BollingerBands(self.data, period=self.params.BB_MA, devfactor=self.params.BB_SD)


    def log(self, txt, doprint=True):
        '''Logs any given text with the time and date as long as doprint=True'''
        date = self.data.datetime.date(0)
        time = self.data.datetime.time(0)
        if doprint:
            print(str(date) + ' ' + str(time) + '--' + txt)


    def notify_order(self, order):
        '''Run on every next iteration. Checks order status and logs accordingly'''
        if order.status in [order.Submitted, order.Accepted]:
            return
        elif order.status == order.Completed:
            if order.isbuy():
                self.log('BUY   price: {}, value: {}, commission: {}'.format(order.executed.price, order.executed.value, order.executed.comm))
            if order.issell():
                self.log('SELL   price: {}, value: {}, commission: {}'.format(order.executed.price, order.executed.value, order.executed.comm))
        elif order.status in [order.Rejected, order.Margin]:
            self.log('Order Rejected/Margin')

        # change order variable back to None to indicate no pending order
        self.order = None
    

    def notify_trade(self, trade):
        '''Run on every next iteration. Logs data on every trade when closed.'''
        if trade.isclosed:
            self.log('CLOSE   Gross P/L: {}, Net P/L: {}'.format(trade.pnl, trade.pnlcomm))

    
    def stop(self):
        '''Runs at the end of the strategy. Logs parameter values and ending value for optimization. Exports data to csv file created in run.py.'''
        self.log('(bbma: {}, bbsd: {}, adxper: {}) Ending Value: {}'.format(self.params.BB_MA, self.params.BB_SD, self.params.ADX_Period, self.broker.getvalue()), doprint=True)
        fields = [[self.params.BB_MA, self.params.BB_SD, self.params.ADX_Period, self.broker.getvalue()]]
        df = pd.DataFrame(data=fields)
        df.to_csv('optimization.csv', mode='a', index=False, header=False)

    def next(self):
        '''Runs for every candlestick. Checks conditions to enter and exit trades.'''
        if self.order:
            return
        
        if self.position.size == 0:
            if self.adx[0] < self.params.ADX_Max:
                if (self.data.close[-1] > self.bb.lines.top[-1]) and (self.data.close[0] <= self.bb.lines.top[0]):
                    self.order = self.sell()
                    self.stopprice = self.bb.lines.top[0]
                    self.closepos = self.buy(exectype=bt.Order.Stop, price=self.stopprice)

                elif (self.data.close[-1] < self.bb.lines.bot[-1]) and (self.data.close[0] >= self.bb.lines.bot[0]):
                    self.order = self.buy()
                    self.stopprice = self.bb.lines.bot[0]
                    self.closepos = self.sell(exectype=bt.Order.Stop, price=self.stopprice)

        elif self.position.size > 0:
            if (self.data.close[-1] < self.bb.lines.mid[-1]) and (self.data.close[0] >= self.bb.lines.mid[0]):
                self.closepos = self.close()
        elif self.position.size < 0:
            if (self.data.close[-1] > self.bb.lines.mid[-1]) and (self.data.close[0] <= self.bb.lines.mid[0]):
                self.closepos = self.close()