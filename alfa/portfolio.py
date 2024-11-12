import sqlite3

class Portfolio:
    def __init__(self, db_name='portfolio.db'):
        # Connect to the database
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        # Initialize tables
        self._create_tables()

    def _create_tables(self):
        """Creates the necessary tables if they don't exist."""
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS stocks (
                                symbol TEXT PRIMARY KEY
                            )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS positions (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                symbol TEXT NOT NULL,
                                shares INTEGER NOT NULL,
                                purchase_price REAL NOT NULL,
                                FOREIGN KEY (symbol) REFERENCES stocks(symbol)
                            )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS watchlist (
                                symbol TEXT PRIMARY KEY,
                                FOREIGN KEY (symbol) REFERENCES stocks(symbol)
                            )''')
        self.conn.commit()

    def _add_to_stock_table(self, symbol):
        """Adds a stock to the stocks table if it doesn't already exist."""
        self.cursor.execute('INSERT OR IGNORE INTO stocks (symbol) VALUES (?)', (symbol,))
        self.conn.commit()

    def add_position(self, symbol, shares, purchase_price):
        """Adds a position to the positions table."""
        # Add to stocks table if not exists
        self._add_to_stock_table(symbol)
        # Insert into positions table
        self.cursor.execute('''INSERT INTO positions (symbol, shares, purchase_price)
                               VALUES (?, ?, ?)''', (symbol, shares, purchase_price))
        self.conn.commit()
        print(f"Added position: {symbol}, Shares: {shares}, Purchase Price: {purchase_price}")

    def remove_position(self, symbol, quantity=None):
        """Removes or reduces the quantity of a position in the positions table."""
        # Check current shares
        self.cursor.execute('SELECT shares FROM positions WHERE symbol = ?', (symbol,))
        result = self.cursor.fetchone()

        if result:
            current_shares = result[0]
            if quantity is None or quantity >= current_shares:
                # Remove the entire position
                self.cursor.execute('DELETE FROM positions WHERE symbol = ?', (symbol,))
                print(f"Removed entire position: {symbol}")
            else:
                # Reduce the quantity of shares
                new_shares = current_shares - quantity
                self.cursor.execute('UPDATE positions SET shares = ? WHERE symbol = ?', (new_shares, symbol))
                print(f"Reduced {symbol} position by {quantity} shares. Remaining shares: {new_shares}")
            self.conn.commit()
        else:
            print(f"Position for {symbol} not found.")

    def add_to_watchlist(self, symbol):
        """Adds a stock to the watchlist table."""
        # Add to stocks table if not exists
        self._add_to_stock_table(symbol)
        # Insert into watchlist table
        self.cursor.execute('INSERT OR IGNORE INTO watchlist (symbol) VALUES (?)', (symbol,))
        self.conn.commit()
        print(f"Added to watchlist: {symbol}")

    def remove_from_watchlist(self, symbol):
        """Removes a stock from the watchlist table."""
        self.cursor.execute('DELETE FROM watchlist WHERE symbol = ?', (symbol,))
        self.conn.commit()
        print(f"Removed from watchlist: {symbol}")

    def get_positions(self):
        """Fetches and returns all positions from the positions table."""
        self.cursor.execute('SELECT symbol, shares, purchase_price FROM positions')
        return self.cursor.fetchall()

    def get_watchlist(self):
        """Fetches and returns all symbols from the watchlist table."""
        self.cursor.execute('SELECT symbol FROM watchlist')
        return [row[0] for row in self.cursor.fetchall()]

    def get_stock_table(self):
        """Fetches and returns all symbols from the stocks table."""
        self.cursor.execute('SELECT symbol FROM stocks')
        return [row[0] for row in self.cursor.fetchall()]

    def close(self):
        """Closes the database connection."""
        self.conn.close()

# Run the main function
if __name__ == "__main__":
    # Example Usage
    portfolio = Portfolio()
    portfolio.add_position("AAPL", 50, 150.0)
    portfolio.add_position("TSLA", 10, 700.0)
    portfolio.remove_position("TSLA", 5)  # Reduces TSLA position by 5 shares
    portfolio.remove_position("AAPL")     # Removes entire AAPL position
    portfolio.add_to_watchlist("GOOGL")
    portfolio.add_to_watchlist("AAPL")
    portfolio.remove_from_watchlist("AAPL")

    # Display current positions, watchlist, and stock table
    print("Positions:", portfolio.get_positions())
    print("Watchlist:", portfolio.get_watchlist())
    print("Stock Table:", portfolio.get_stock_table())

    # Close the connection
    portfolio.close()