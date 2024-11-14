#
# TODOs:
# [] unit tests
# [] db connection 
# [] connect positions/portfolio to db
# [] connect stock to yfinance and db
# [] cash position
# quantity +/- buy/sell
#


class Symbol

class Portfolio:
    def __init__(self, name):
        self.name = name
        self.account
        self.positions = {}
        self.following = []
        self.transactions = []

        # try to load from db (including watchlist and positions)
        # if not present insert

    def get_all_positions(self):
        return self.positions

    def add_position(self, symbol, quantity):
        # if exist update quantity / otherwise insert / add inmemory and db
        pass

    def remove_position(self, symbol, quantity):
        # if quantity > current delete / if not deduct / both memory and db
        pass

    def get_watchlist(self):
        return self.watchlist
    
    def start_watching(self, symbol):
        pass

    def stop_watching(self, symbol):
        pass

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
