# CREATE TABLE IF NOT EXISTS stock (
#     id INTEGER PRIMARY KEY,
#     symbol TEXT NOT NULL UNIQUE,
#     name TEXT NOT NULL
#     );

# CREATE TABLE IF NOT EXISTS price (
#     id INTEGER PRIMARY KEY,
#     stock_id INTEGER,
#     date NOT NULL,
#     open NOT NULL,
#     high NOT NULL,
#     low NOT NULL,
#     close NOT NULL,
#     adjusted_close NOT NULL,
#     volume NOT NULL,
#     FOREIGN KEY (stock_id) REFERENCES stock (id)
#     );

# CREATE TABLE IF NOT EXISTS portfolio (
#     id INTEGER PRIMARY KEY,
#     name TEXT NOT NULL UNIQUE,
#     currency TEXT NOT NULL UNIQUE
#     );

# CREATE TABLE IF NOT EXISTS stock_to_watch (
#     id INTEGER PRIMARY KEY,
#     stock_id INTEGER,
#     symbol TEXT NOT NULL UNIQUE,
#     portfolio_id INTEGER,
#     FOREIGN KEY (portfolio_id) REFERENCES portfolio (id),
#     FOREIGN KEY (stock_id) REFERENCES stock (id)
#     );

# CREATE TABLE IF NOT EXISTS transaction_ledger (
#     id INTEGER PRIMARY KEY,
#     external_id INTEGER NOT NULL UNIQUE,
#     portfolio_id INTEGER,
#     timestamp INTEGER NOT NULL,
#     stock_id INTEGER,
#     quantity NOT NULL,
#     price NOT NULL,
#     type NOT NULL, -- BUY, SELL, DEPOSIT_STOCK
#     fees NOT NULL,
#     FOREIGN KEY (portfolio_id) REFERENCES portfolio (id),
#     FOREIGN KEY (stock_id) REFERENCES stock (id)
#     );

# CREATE TABLE IF NOT EXISTS cash_ledger (
#     id INTEGER PRIMARY KEY,
#     external_id INTEGER NOT NULL UNIQUE,
#     portfolio_id INTEGER,
#     timestamp INTEGER NOT NULL,
#     amount NOT NULL,
#     type NOT NULL, -- DEPOSIT / WITHDRAW
#     balance NOT NULL,
#     FOREIGN KEY (portfolio_id) REFERENCES portfolio (id)
#     );

# CREATE TABLE IF NOT EXISTS last_processed_batch (
#     location TEXT PRIMARY KEY,
#     batch NOT NULL UNIQUE
#     );

# CREATE TABLE IF NOT EXISTS end_of_day_position (
#     id INTEGER PRIMARY KEY,
#     portfolio_id INTEGER,
#     stock_id INTEGER,
#     symbol TEXT NOT NULL UNIQUE,
#     date NOT NULL,
#     size NOT NULL,
#     average_price NOT NULL,
#     FOREIGN KEY (portfolio_id) REFERENCES portfolio (id),
#     FOREIGN KEY (stock_id) REFERENCES stock (id)
#     );

from peewee import DateField, FloatField, ForeignKeyField, IntegerField, Model, SqliteDatabase, TextField

from alfa.config import log, settings
from alfa.util import create_directories_for_path

db = SqliteDatabase(None)


def open_db():
    path = settings.DB_PATH
    log.info(f"Initializing database from {path}")
    create_directories_for_path(path)
    db.init(path)
    return db


class BaseModel(Model):
    class Meta:
        database = db


# Stock model
class Stock(BaseModel):
    id = IntegerField(primary_key=True)
    symbol = TextField(unique=True, null=False)
    name = TextField(null=False)

    @staticmethod
    def add_stock(symbol, name):
        """
        Add a new stock to the database.

        :param symbol: The stock symbol (e.g., "AAPL").
        :param name: The stock name (e.g., "Apple Inc.").
        :return: The created Stock object or None if an error occurred.
        """
        try:
            stock = Stock.create(symbol=symbol, name=name)
            log.debug(f"Stock with symbol '{symbol}' was successfully added.")
            return stock
        except Exception as e:
            log.error(f"Error adding {symbol}. {e}")
            return None

    @staticmethod
    def get_stocks():
        """
        Retrieve all stocks from the database.

        :return: A list of Stock objects.
        """
        try:
            stocks = list(Stock.select())
            log.debug(f"Found {len(stocks)} stocks.")
            return stocks
        except Exception as e:  # pragma: no cover
            log.error(f"Error retrieving stocks. {e}")
            return []

    @staticmethod
    def delete_stock(symbol):
        """
        Delete a stock by its symbol.

        :param symbol: The stock symbol to delete (e.g., "AAPL").
        :return: True if deletion was successful, False otherwise.
        """
        try:
            query = Stock.delete().where(Stock.symbol == symbol)
            rows_deleted = query.execute()
            if rows_deleted > 0:
                log.debug(f"Stock with symbol '{symbol}' was successfully deleted.")
                return True
            else:
                log.warning(f"Stock with symbol '{symbol}' not found.")
                return False
        except Exception as e:  # pragma: no cover
            log.error(f"Error deleting stock {symbol}. {e}")
            return False


class Price(BaseModel):
    id = IntegerField(primary_key=True)
    stock_id = ForeignKeyField(Stock, backref="prices", on_delete="CASCADE")
    symbol = TextField(null=False)
    date = DateField(null=False)
    open = FloatField(null=False)
    high = FloatField(null=False)
    low = FloatField(null=False)
    close = FloatField(null=False)
    adjusted_close = FloatField(null=False)
    volume = IntegerField(null=False)

    @staticmethod
    def add_price(symbol, date, open, high, low, close, adjusted_close, volume):
        """
        Adds a price entry for a given stock symbol.

        :param symbol: The stock symbol (e.g., "AAPL").
        :param date: The date of the price.
        :param open: The opening price.
        :param high: The highest price.
        :param low: The lowest price.
        :param close: The closing price.
        :param adjusted_close: The adjusted closing price.
        :param volume: The volume of the stock traded.
        :return: The created Price object or None if an error occurred.
        """
        try:
            stock = Stock.get(Stock.symbol == symbol)
            price = Price.create(
                stock_id=stock.id,
                symbol=symbol,
                date=date,
                open=open,
                high=high,
                low=low,
                close=close,
                adjusted_close=adjusted_close,
                volume=volume,
            )
            log.debug(f"Price for symbol '{symbol}' on {date} was successfully added.")
            return price
        except Exception as e:  # pragma: no cover
            log.error(f"Error adding price for {symbol}. {e}")
            return None

    @staticmethod
    def get_prices_by_symbol(symbol):
        """
        Retrieve all prices for a given symbol from oldest to newest.

        :return: A list of Price objects.
        """
        try:
            prices = list(Price.select().where(Price.symbol == symbol).order_by(Price.date.asc()))
            log.debug(f"Found {len(prices)} prices for {symbol}.")
            return prices
        except Exception as e:  # pragma: no cover
            log.error(f"Error retrieving prices. {e}")
            return []

    @staticmethod
    def get_latest_date_by_symbol(symbol):
        """
        Gets the most recent date for a given stock symbol.

        :param symbol: The stock symbol (e.g., "AAPL").
        :return: The most recent date as a DateField object, or None if no data exists.
        """
        try:
            recent_price = Price.select().where(Price.symbol == symbol).order_by(Price.date.desc()).first()
            return recent_price.date if recent_price else None
        except Exception as e:  # pragma: no cover
            log.error(f"Error retrieving most recent date for {symbol}. {e}")
            return None

    @staticmethod
    def get_all_symbols_with_latest_date():
        """
        Gets all stock symbols with their most recent dates.

        :return: A dictionary of {symbol: most_recent_date}.
        """
        try:
            query = (
                Price.select(Price.symbol, Price.date).distinct().order_by(Price.symbol, Price.date.desc())
            )
            result = {}
            for row in query:
                if row.symbol not in result or result[row.symbol] < row.date:
                    result[row.symbol] = row.date
            return result
        except Exception as e:  # pragma: no cover
            log.error(f"Error retrieving stocks with most recent dates. {e}")
            return {}
