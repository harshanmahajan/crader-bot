# Crader: Stock Trading Bot

Crader is an automated stock trading bot that bases its decisions on Jim Cramer's stock picks from the TV show *Mad Money*, and selects and trades stocks using a combination of web scraping, sentiment analysis, and algorithmic trading strategies.

## Technologies Used

- **[Lumibot](https://lumibot.com/)**: Utilized in developing and running the trading bot.
- **[Alpaca API](https://alpaca.markets/)**: Used by Lumibot to connect to the stock market and submit orders.
- **[PyTorch](https://pytorch.org/)**: Used for performing sentiment analysis on related news headlines using the FinBERT model to improve prediction.
- **[BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)**: Utilized for web scraping up-to-date stock picks from [Quiver Quant](https://www.quiverquant.com/home/) to gather the latest data on tickers and their projected direction.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/harshanmahajan/crader-bot.git
   cd crader-bot
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your API keys:
   - Obtain an Alpaca API key and secret from [Alpaca](https://alpaca.markets/).

## Usage

   ```bash
   python craderbot.py
   ```

   To backtest using the data in cramerpicks.csv:
   - Make sure to specify get_symbols_backtesting() rather than get_symbols() in the on_trading_iteration() definition
   - Select the start_date and end_date variables in craderbot.py accordingly. 

## Sources

I used [this tutorial](https://www.youtube.com/watch?v=c9OjEThuJjY) by Nicholas Renotte to get started developing this bot, and used his implementation of sentiment analysis in news_processing.py

## Disclaimer

This project was made for educational purposes only. Trading stocks involves substantial risk, and there is no guarantee of profit. Use at your own risk.
