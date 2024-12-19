from lumibot.brokers import Alpaca
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from datetime import datetime
from alpaca_trade_api import REST
from timedelta import Timedelta
from news_processing import estimate_sentiment
import requests
from bs4 import BeautifulSoup
import pandas as pd
import math

API_KEY = 'API_KEY_HERE'
API_SECRET = 'API_SECRET_HERE'
BASE_URL = 'https://paper-api.alpaca.markets/v2'

ALPACA_CONFIG = {
    'API_KEY' : API_KEY,
    'API_SECRET' : API_SECRET,
    'PAPER' : True
}

#trading logic defined here
class Crader(Strategy):
    def initialize(self):
        self.sleeptime = '1D'
        self.last_trade = None
        self.api = REST(base_url=BASE_URL, key_id=API_KEY, secret_key=API_SECRET)
        self.picks = pd.read_csv('cramerpicks.csv') #2016-2022 data for backtesting
        self.weights = {
            'Buy': 1.0,
            'Sell': -1.0,
            'Bearish': -1.0,
            'Not Recommending': -0.5,
            'Bullish': 0.8,
            'Start a Small Position': 0.2,
            'Buy on a Pullback': 0.5,
            'Hold': 0.0,
            'Long': 0.9,
            'Sell on a Pop': -0.5,
            'Speculative - Good': 0.7,
            'Speculative - Bad': -0.7,
            'Trim': -0.3
        }

    #Only used for backtesting with 2016 - 2022 kaggle data
    def get_symbols_backtesting(self, today):
        #select data for specified day
        df = self.picks
        df = df[df['Date'] == today]
        
        #identify buys and sells
        buys = {}
        sells = {}
        for index, row in df.iterrows():
            ticker = row['Ticker']
            call = row['Call']
            if call == 'Buy': buys[ticker] = 1 
            elif call == 'Positive Mention': buys[ticker] = 0.5
            elif call == 'Sell': sells[ticker] = 1
            elif call == 'Negative Mention': sells[ticker] = 0.5

        return buys,sells

    def get_symbols(self, today):
        today = datetime.strptime(today, "%Y-%m-%d").strftime("%b. %d, %Y")
        #put today's picks from quiver in picks array
        res = requests.get('https://www.quiverquant.com/cramertracker/')
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.find('div', class_='holdings-table').find('tbody')
        picks = []

        for tr in rows.find_all('tr'):
            tds = tr.find_all('td')
            
            #get ticker, direction, date information
            date = tds[2].text.strip() if tds[2] else None
            if date != today: 
                continue
            ticker = tds[0].find('a').text.strip() if tds[0] else None
            direction = tds[1].text.strip() if tds[1] else None
            if ticker and direction: picks.append((ticker, direction))

        schema = ['ticker', 'direction']
        df = pd.DataFrame(picks, columns=schema)

        buys = {}
        sells = {}        
        # identify buys and sells
        for index, row in df.iterrows():
            ticker = row['ticker']
            direction = row['direction']
            if direction in self.weights.keys() and self.weights[direction] > 0:
                buys[ticker] = self.weights[direction]
            elif direction in self.weights.keys() and self.weights[direction] < 0:
                sells[ticker] = self.weights[direction]
        return buys, sells 

    #get start and end date for news articles
    def get_dates(self):
        three_days_prior = self.prevDay - Timedelta(days=3)
        return self.prevDay.strftime('%Y-%m-%d'), three_days_prior.strftime('%Y-%m-%d')
    
    #get sentiment of news articles for a given symbol from start to end date from finbert
    def get_sentiment(self, symbol):
        prevDay, three_days_prior = self.get_dates()
        news = self.api.get_news(symbol=symbol, start=three_days_prior, end=prevDay)
        news = [ev.__dict__['_raw']['headline'] for ev in news]
        probability, sentiment = estimate_sentiment(news)
        return probability, sentiment 

    def on_trading_iteration(self):
        today = self.get_datetime()
        self.prevDay = today - Timedelta(days=3) if today.weekday() == 0 else today - Timedelta(days=1) 
        
        #collect symbols for a the previous day in string format
        buys, sells = self.get_symbols_backtesting(self.prevDay.strftime('%Y-%m-%d'))
        
        #get all currently held positions
        held = {}
        for e in self.get_positions():
            held[e.asset] = e.quantity

        #sell all stocks marked negatively
        for symbol, weight in sells.items():
            #if symbol is in currently held stocks, sell off the weight %age of that stock
            if symbol in held.keys():
                probability, sentiment = self.get_sentiment(symbol)
                if sentiment == 'negative' and probability > 0.98:                  
                    quantity = math.ceil(weight * held[symbol])
                    order = self.create_order(
                        symbol, 
                        quantity, 
                        'sell', 
                        type = 'market' 
                    )
                    self.submit_order(order)
        
        #create dict mapping symbol to its last price
        prices = {}
        for symbol, weight in buys.items():
            last_price = self.get_last_price(symbol)
            if last_price:
                prices[symbol] = last_price

        #calculate total weight
        cash = self.get_cash()
        total_weight = 0
        for symbol in prices.keys():
            total_weight += buys[symbol]

        cash_per = cash / total_weight if total_weight != 0 else 0
        
        #buy all stocks marked positively (according to weight)
        for symbol, price in prices.items():
            weight = buys[symbol]
            #if symbol not on market, skip
            if cash_per * weight >= price:
                probability, sentiment = self.get_sentiment(symbol)
                if sentiment == 'positive' and probability > 0.98:
                    quantity = math.floor(weight * cash_per / price)
                    order = self.create_order(
                        symbol, 
                        quantity, 
                        'buy', 
                        type='bracket', 
                        take_profit_price = price * 1.20,
                        stop_loss_price = price * 0.85
                    )
                    self.submit_order(order)

strategy = Crader(broker = Alpaca(ALPACA_CONFIG))

#Dates available on Quiver 
start_date = datetime(2024,11,16)
end_date = datetime(2024,12,18)

strategy.backtest(YahooDataBacktesting, start_date, end_date)

# trader = Trader()
# trader.add_strategy(strategy)
# trader.run_all()