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

from enum import Enum

from peewee import DateTimeField, FloatField, ForeignKeyField, IntegerField, Model, SqliteDatabase, TextField

from alfa.config import log, settings
from alfa.util import create_directories_for_path

db = SqliteDatabase(None, pragmas={"foreign_keys": 1})


def open_db():
    path = settings.DB_PATH
    log.debug(f"Initializing database {path}")
    create_directories_for_path(path)
    db.init(path)
    return db


class BaseModel(Model):
    class Meta:
        database = db

    @staticmethod
    def get_models():
        """
        Lists all direct subclasses (models) of BaseModel.
        :return: A list of model classes.
        """
        return BaseModel.__subclasses__()


# Stock model
class Stock(BaseModel):
    id = IntegerField(primary_key=True)
    symbol = TextField(unique=True, null=False)
    name = TextField(null=True)

    @staticmethod
    def add_stock(symbol, name=None):
        """
        Add a new stock to the database.

        :param symbol: The stock symbol (e.g., "AAPL").
        :param name: The stock name (e.g., "Apple Inc.").
        :return: The created Stock object or None if an error occurred.
        """
        try:
            stock = Stock.create(symbol=symbol, name=name)
            log.debug(f"Stock with symbol {symbol} was successfully added.")
            return stock
        except Exception as e:  # pragma: no cover
            log.error(f"Error adding {symbol}. {e}")
            return None

    def get_most_recent_price(self):
        """
        Retrieves the most recent price entry for the stock.

        This method queries the related `Price` entries for the stock,
        orders them by timestamp in descending order, and returns the latest price.

        :return: The most recent `Price` object for the stock, or None if no prices are available.
        :rtype: Price or None
        """
        price = self.prices.order_by(Price.timestamp.desc()).first()
        if price:
            log.debug(f"{self.symbol} most recent price is from {price.timestamp}.")
        else:
            log.debug(f"{self.symbol} has no prices.")
        return price

    def add_price(self, timestamp, open, high, low, close, adjusted_close, volume):
        """
        Adds a price entry for this stock.

        :param timestamp: The timestamp of the price.
        :param open: The opening price.
        :param high: The highest price.
        :param low: The lowest price.
        :param close: The closing price.
        :param adjusted_close: The adjusted closing price.
        :param volume: The volume of the stock traded.
        :return: The created Price object or None if an error occurred.
        """
        try:
            price = Price.create(
                stock_id=self.id,
                symbol=self.symbol,
                timestamp=timestamp,
                open=open,
                high=high,
                low=low,
                close=close,
                adjusted_close=adjusted_close,
                volume=volume,
            )
            log.debug(f"Price for symbol {self.symbol} on {timestamp} was successfully added.")
            return price
        except Exception as e:  # pragma: no cover
            log.error(f"Error adding price for {self.symbol}. {e}")
            return None


class Price(BaseModel):
    id = IntegerField(primary_key=True)
    stock_id = ForeignKeyField(Stock, backref="prices", on_delete="CASCADE")
    symbol = TextField(null=False)
    timestamp = DateTimeField(null=False)
    open = FloatField(null=False)
    high = FloatField(null=False)
    low = FloatField(null=False)
    close = FloatField(null=False)
    adjusted_close = FloatField(null=False)
    volume = IntegerField(null=False)


class Currency(Enum):
    CAD = "Canadian Dollar"
    USD = "US Dollar"


class Portfolio(BaseModel):
    id = IntegerField(primary_key=True)
    name = TextField(unique=True, null=False)
    currency = TextField(unique=True, null=False)

    @staticmethod
    def add_portfolio(name, currency=Currency.USD):
        """
        Adds a new portfolio to the database.

        :param name: The name of the portfolio.
        :param currency: The currency of the portfolio. Defaults to USD
        :return: The created Portfolio object, or None if an error occurs.
        """
        try:
            portfolio = Portfolio.create(name=name, currency=currency.name)
            log.debug(f"Portfolio {name} in {currency} was succesfully added .")
            return portfolio
        except Exception as e:
            log.error(f"Error adding portfolio {name}. {e}")
            return None

    @staticmethod
    def get_portfolios():
        """
        Retrieves all portfolios from the database.

        :return: A list of Portfolio objects.
        """
        return list(Portfolio.select())

    def get_currency(self):
        """
        Retrieves the currency as a Currency enum instance.

        :return: A Currency enum instance corresponding to the `self.currency` attribute.
        :raises KeyError: If `self.currency` does not match any Currency enum member.
        """
        return Currency[self.currency]

    def start_watching(self, symbol, name=None):
        """
        Adds a stock to the watchlist for the current portfolio.

        This method first checks if the stock is already in the watchlist for the portfolio.
        If the stock is not in the watchlist, it tries to retrieve the stock from the `Stock` model.
        If the stock does not exist, it creates a new stock entry before adding it to the watchlist.

        :param symbol: The symbol of the stock to start watching (e.g., "AAPL").
        :param name: Optional. The name of the stock to start watching (e.g., "Apple Inc.").
                    If the stock does not exist, this name will be used to create a new stock entry.
        :return:
            - True if the stock was successfully added to the watchlist.
            - False if the stock is already being watched or if an error occurred.
        :rtype: bool
        """
        try:
            query = StockToWatch.select().where(
                (StockToWatch.symbol == symbol) & (StockToWatch.portfolio_id == self.id)
            )
            if query.exists():
                log.debug(f"{self.name} is already watching {symbol}.")
                return True

            stock = Stock.get_or_none(Stock.symbol == symbol)
            if not stock:
                log.debug(f"Add stock {symbol} to watch for {self.name}.")
                stock = Stock.create(symbol=symbol, name=name)
                log.debug(f"{symbol} was successfully added.")

            StockToWatch.create(
                stock_id=stock.id,
                symbol=symbol,
                portfolio_id=self.id,
            )
            log.debug(f"{self.name} started watching {symbol}.")
            return True
        except Exception as e:
            log.error(f"Failed to start watching {symbol} for portfolio {self.name}. {e}")
            return False

    def stop_watching(self, symbol):
        """
        Deletes a StockToWatch entry for a specific portfolio and stock symbol.

        :param symbol: The symbol of the stock to delete (e.g., "AAPL").
        :return: True if the stock was successfully removed from the watchlist,
                False if the stock is not being watched or if an error occurred.
        """
        try:
            query = StockToWatch.delete().where(
                (StockToWatch.symbol == symbol) & (StockToWatch.portfolio_id == self.id)
            )
            rows_deleted = query.execute()
            if rows_deleted > 0:
                log.debug(f"Stock {symbol} successfully deleted from portfolio {self.name}.")
                return True
            log.debug(f"No stock {symbol} found in portfolio {self.name}.")
            return False
        except Exception as e:
            log.error(f"Failed to stop watching {symbol} for portfolio {self.name}. {e}")
            return False


class StockToWatch(BaseModel):
    id = IntegerField(primary_key=True)
    stock_id = ForeignKeyField(Stock, null=False)
    symbol = TextField(unique=False, null=False)
    portfolio_id = ForeignKeyField(Portfolio, backref="watchlist", on_delete="CASCADE")

    class Meta:
        table_name = "stock_to_watch"
