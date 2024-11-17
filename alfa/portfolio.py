from dynaconf import settings
from alfa.util import get_logger

class Portfolio:

    def __init__(self, name=None):
        self.name = name or settings.PORTFOLIO_NAME
        self.cash = 0
        self.positions = {}
        self.stocks_to_watch = []

    def get_all_positions(self):
        return self.positions

    def get_position_size(self, symbol):
        symbol = symbol.upper()
        return 0 if symbol not in self.positions else self.positions[symbol]['size']

    def get_cash_balance(self):
        return self.cash

    def sell(self, symbol, qty, price):
        symbol = symbol.upper()
        if self.get_position_size(symbol) == 0:
            # get_logger().error(f"Portfolio {self.name} has no position in {symbol}.")
            return False

        size = self.positions[symbol]["size"]

        if qty > size:
            # Limit to position size
            get_logger().info(
                f"Requested quantity {qty} is capped at {size} {symbol} by {self.name}'s position size."
            )
            qty = size
        # New position size
        size -= qty

        if size == 0:
            # Liquidate position
            self.positions.pop(symbol)
        else:
            # Update position size
            self.positions[symbol]["size"] = size

        self.cash += qty * price

        get_logger().info(f"Transaction - SELL {qty} {symbol} @ {price}")

    def buy(self, symbol, qty, price):
        symbol = symbol.upper()

        # TODO: check cash balance first

        if self.get_position_size(symbol) == 0:
            # Initialize position
            self.positions[symbol] = {"size": 0, "average_price": 0.0}

        size = self.positions[symbol]["size"]
        average_price = self.positions[symbol]["average_price"]

        # New position size
        new_size = size + qty

        # Update position with weighted average price
        self.positions[symbol]["average_price"] = (
            average_price * size + price * qty
        ) / new_size
        # Update position size
        self.positions[symbol]["size"] = new_size

        get_logger().info(f"Transaction - BUY {qty} {symbol} @ {price}")

    def withdraw(self, amount):
        pass

    def withdraw_stock(self, symbol, qty):
        symbol = symbol.upper()
        pass

    def deposit(self, amount):
        pass

    def deposit_stock(self, symbol, qty):
        symbol = symbol.upper()
        pass


# import yfinance as yf
# import numpy as np
# import pandas as pd
# from datetime import datetime, timedelta
# import statsmodels.api as sm

# def calculate_alpha(risk_free_rate, start_date, end_date):
#     # Define portfolio and benchmark
#     tickers = ['TSLA', 'IBIT']
#     benchmark_ticker = 'SPY'
#     shares = [100, 100]

#     # Download data
#     data = yf.download(tickers + [benchmark_ticker], start=start_date, end=end_date)['Adj Close']

#     # Calculate daily returns
#     returns = data.pct_change().dropna()

#     # Calculate individual betas
#     betas = {}
#     for ticker in tickers:
#         # Run regression of stock returns vs. benchmark returns
#         X = returns[benchmark_ticker]
#         y = returns[ticker]
#         X = sm.add_constant(X)
#         model = sm.OLS(y, X).fit()
#         betas[ticker] = model.params[benchmark_ticker]

#     # Calculate portfolio beta as weighted average of individual betas
#     total_value = sum([shares[i] * data[ticker].iloc[-1] for i, ticker in enumerate(tickers)])
#     weights = [(shares[i] * data[ticker].iloc[-1]) / total_value for i, ticker in enumerate(tickers)]
#     portfolio_beta = sum([weights[i] * betas[ticker] for i, ticker in enumerate(tickers)])

#     # Calculate portfolio return and benchmark return over the period
#     portfolio_return = sum([weights[i] * returns[ticker].mean() for i, ticker in enumerate(tickers)]) * len(returns)
#     benchmark_return = returns[benchmark_ticker].mean() * len(returns)

#     # Calculate alpha
#     alpha = portfolio_return - (risk_free_rate + portfolio_beta * (benchmark_return - risk_free_rate))

#     return alpha

# # Example usage
# risk_free_rate = 0.02  # Annual risk-free rate, e.g., 2%
# start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
# end_date = datetime.now().strftime('%Y-%m-%d')

# alpha = calculate_alpha(risk_free_rate, start_date, end_date)
# print(f"Alpha of the portfolio: {alpha:.2%}")


#
# TODOs:
# [] unit tests
# [] db connection
# [] connect positions/portfolio to db
# [] connect stock to yfinance and db
# [] cash position
# quantity +/- buy/sell
#
# import sqlite3


# def get_all_symbols(cursor):
#     cursor.execute('SELECT * FROM symbol')
#     rows = cursor.fetchall()
#     return [dict(row) for row in rows]

# def add_symbol(cursor, symbol, name):
#     try:
#         cursor.execute('''
#             INSERT INTO symbol (symbol, name) VALUES (?, ?)
#         ''', (symbol, name))
#     except sqlite3.IntegrityError:
#         print(f"Symbol '{symbol}' already exists in the database.")

# def delete_symbol(cursor, symbol):
#     cursor.execute('DELETE FROM symbol WHERE symbol = ?', (symbol,))
#     self.connection.commit()
#     if self.cursor.rowcount == 0:
#         print(f"Symbol '{symbol}' not found in the database.")
#     else:
#         print(f"Symbol '{symbol}' has been deleted from the database.")


# def get_all_portfolios():
#     return []


# class Symbol:
#     CREATE_TABLE_SQL = '''
#         CREATE TABLE IF NOT EXISTS symbol (
#             id INTEGER PRIMARY KEY,
#             symbol TEXT NOT NULL UNIQUE,
#             name TEXT NOT NULL
#         );
#     '''

#     def __init__(self, connection, cursor):
#         self.connection = connection
#         self.cursor = cursor

#     def add_symbol()

# class Portfolio:
#     def __init__(self, name):
#         self.name = name
#         self.account
#         self.positions = {}
#         self.following = []
#         self.transactions = []

#         # try to load from db (including watchlist and positions)
#         # if not present insert

#     def get_all_positions(self):
#         return self.positions

#     def add_position(self, symbol, quantity):
#         # if exist update quantity / otherwise insert / add inmemory and db
#         pass

#     def remove_position(self, symbol, quantity):
#         # if quantity > current delete / if not deduct / both memory and db
#         pass

#     def get_watchlist(self):
#         return self.watchlist

#     def start_watching(self, symbol):
#         pass

#     def stop_watching(self, symbol):
#         pass

# import sqlite3
# from datetime import datetime

# class Portfolio:
#     def __init__(self, db_name="portfolio.db", portfolio_id=None, name=None):
#         self.conn = sqlite3.connect(db_name)
#         self.create_tables()

#         if portfolio_id:
#             # Load existing portfolio
#             portfolio = self.get_portfolio_by_id(portfolio_id)
#             if not portfolio:
#                 raise ValueError(f"Portfolio with id {portfolio_id} does not exist.")
#             self.id = portfolio_id
#             self.name = portfolio[1]
#         elif name:
#             # Create a new portfolio
#             self.id = self.create_portfolio(name)
#             self.name = name
#         else:
#             raise ValueError("You must provide either a portfolio_id or a name.")

#     def create_tables(self):
#         with self.conn:
#             # Creating tables if they don't exist
#             self.conn.execute('''
#             CREATE TABLE IF NOT EXISTS stock (
#                 id INTEGER PRIMARY KEY,
#                 symbol TEXT NOT NULL UNIQUE,
#                 name TEXT NOT NULL
#             )''')

#             self.conn.execute('''
#             CREATE TABLE IF NOT EXISTS price (
#                 id INTEGER PRIMARY KEY,
#                 stock_id INTEGER,
#                 date TEXT NOT NULL,
#                 open REAL NOT NULL,
#                 high REAL NOT NULL,
#                 low REAL NOT NULL,
#                 close REAL NOT NULL,
#                 adjusted_close REAL NOT NULL,
#                 volume INTEGER NOT NULL,
#                 FOREIGN KEY (stock_id) REFERENCES stock (id)
#             )''')

#             self.conn.execute('''
#             CREATE TABLE IF NOT EXISTS portfolio (
#                 id INTEGER PRIMARY KEY,
#                 name TEXT NOT NULL UNIQUE,
#                 watchlist_id INTEGER,
#                 FOREIGN KEY (watchlist_id) REFERENCES watchlist (id)
#             )''')

#             self.conn.execute('''
#             CREATE TABLE IF NOT EXISTS watchlist (
#                 id INTEGER PRIMARY KEY,
#                 stock_id INTEGER,
#                 FOREIGN KEY (stock_id) REFERENCES stock (id)
#             )''')

#             self.conn.execute('''
#             CREATE TABLE IF NOT EXISTS position (
#                 id INTEGER PRIMARY KEY,
#                 portfolio_id INTEGER,
#                 stock_id INTEGER,
#                 date TEXT NOT NULL,
#                 quantity REAL NOT NULL,
#                 FOREIGN KEY (portfolio_id) REFERENCES portfolio (id),
#                 FOREIGN KEY (stock_id) REFERENCES stock (id)
#             )''')

#     def create_portfolio(self, name):
#         """Create a new portfolio."""
#         with self.conn:
#             cursor = self.conn.execute(
#                 "INSERT INTO portfolio (name) VALUES (?)",
#                 (name,)
#             )
#             return cursor.lastrowid

#     def get_portfolio_by_id(self, portfolio_id):
#         """Retrieve a portfolio by ID."""
#         cursor = self.conn.cursor()
#         cursor.execute("SELECT * FROM portfolio WHERE id = ?", (portfolio_id,))
#         return cursor.fetchone()

#     def add_position(self, stock_id, quantity, date=None):
#         """Add a new position to this portfolio."""
#         if date is None:
#             date = datetime.now().strftime("%Y-%m-%d")
#         with self.conn:
#             self.conn.execute(
#                 '''
#                 INSERT INTO position (portfolio_id, stock_id, date, quantity)
#                 VALUES (?, ?, ?, ?)
#                 ''', (self.id, stock_id, date, quantity)
#             )

#     def get_all_positions(self):
#         """Retrieve all positions in this portfolio, including stock information."""
#         cursor = self.conn.cursor()
#         cursor.execute('''
#             SELECT position.id, stock.symbol, stock.name, position.date, position.quantity
#             FROM position
#             JOIN stock ON position.stock_id = stock.id
#             WHERE position.portfolio_id = ?
#         ''', (self.id,))
#         return cursor.fetchall()

#     def close(self):
#         """Close the database connection."""
#         self.conn.close()

# # Example usage
# if __name__ == "__main__":
#     # Create or load a portfolio by name
#     portfolio = Portfolio(name="My Portfolio")

#     # Add a position (assuming stock_id=1 exists)
#     portfolio.add_position(stock_id=1, quantity=100)

#     # Retrieve all positions
#     positions = portfolio.get_all_positions()
#     for pos in positions:
#         print(pos)

#     # Close the connection
#     portfolio.close()
