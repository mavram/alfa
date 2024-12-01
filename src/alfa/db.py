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

        Returns:
            list: A list of model classes.
        """
        return BaseModel.__subclasses__()


class Stock(BaseModel):
    id = IntegerField(primary_key=True)
    symbol = TextField(unique=True)
    name = TextField(null=True)

    @staticmethod
    def add_stock(symbol, name=None):
        """
        Adds a new stock to the database.

        Args:
            symbol (str): The stock symbol (e.g., "AAPL").
            name (str, optional): The stock name (e.g., "Apple Inc."). Defaults to None.

        Returns:
            Stock or None: The created Stock object, or None if an error occurred.
        """
        try:
            if not symbol:
                raise ValueError("Symbol cannot be empty.")
            stock = Stock.create(symbol=symbol, name=name)
            log.debug(f"Stock with symbol {symbol} was successfully added.")
            return stock
        except Exception as e:  # pragma: no cover
            log.error(f"Error adding {symbol}. {e}")
            return None

    def get_most_recent_price(self):
        """
        Retrieves the most recent price entry for the stock.

        Returns:
            Price or None: The most recent Price object for the stock, or None if no prices are available.
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

        Args:
            timestamp (UTC epoch time): The timestamp of the price.
            open (float): The opening price.
            high (float): The highest price.
            low (float): The lowest price.
            close (float): The closing price.
            adjusted_close (float): The adjusted closing price.
            volume (int): The volume of the stock traded.

        Returns:
            Price or None: The created Price object, or None if an error occurred.
        """
        try:
            if volume < 0:
                raise ValueError("Volume cannot be negative.")

            price = Price.create(
                stock=self,
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
    stock = ForeignKeyField(Stock, field="id", backref="prices", on_delete="CASCADE")
    symbol = TextField()
    timestamp = DateTimeField()
    open = FloatField()
    high = FloatField()
    low = FloatField()
    close = FloatField()
    adjusted_close = FloatField()
    volume = IntegerField()


class CurrencyType(Enum):
    CAD = "Canadian Dollar"
    USD = "US Dollar"


class TransactionType(str, Enum):
    BUY = "BUY"
    DEPOSIT = "DEPOSIT"
    DEPOSIT_STOCK = "DEPOSIT_STOCK"
    SELL = "SELL"
    WITHDRAW = "WITHDRAW"


class Portfolio(BaseModel):
    id = IntegerField(primary_key=True)
    name = TextField(unique=True)
    currency = TextField(
        choices=[c.name for c in CurrencyType],
    )
    cash = FloatField(default=0.0)

    @staticmethod
    def add_portfolio(name, currency=CurrencyType.USD):
        """
        Adds a new portfolio to the database.

        Args:
            name (str): The name of the portfolio.
            currency (CurrencyType, optional): The currency of the portfolio. Defaults to CurrencyType.USD.

        Returns:
            Portfolio or None: The created Portfolio object, or None if an error occurs.
        """
        try:
            portfolio = Portfolio.create(name=name, currency=currency.name)
            log.debug(f"Portfolio {name} in {currency.name} was successfully added.")
            return portfolio
        except Exception as e:
            log.error(f"Error adding portfolio {name}. {e}")
            return None

    @staticmethod
    def get_portfolios():
        """
        Retrieves all portfolios from the database.

        Returns:
            list: A list of Portfolio objects.
        """
        return list(Portfolio.select())

    def get_currency(self):
        """
        Retrieves the currency as a CurrencyType enum instance.

        Returns:
            CurrencyType: A CurrencyType enum instance corresponding to the `self.currency` attribute.

        Raises:
            KeyError: If `self.currency` does not match any CurrencyType enum member.
        """
        return CurrencyType[self.currency]

    def start_watching(self, symbol, name=None):
        """
        Adds a stock to the watchlist for the current portfolio.

        This method first checks if the stock is already in the watchlist for the portfolio.
        If the stock is not in the watchlist, it tries to retrieve the stock from the `Stock` model.
        If the stock does not exist, it creates a new stock entry before adding it to the watchlist.

        Args:
            symbol (str): The symbol of the stock to start watching (e.g., "AAPL").
            name (str, optional): The name of the stock (e.g., "Apple Inc."). Defaults to None.

        Returns:
            bool: True if the stock was successfully added to the watchlist, False otherwise.
        """
        try:
            query = (
                StockToWatch.select()
                .join(Stock)
                .where((Stock.symbol == symbol) & (StockToWatch.portfolio == self))
            )

            if query.exists():
                log.debug(f"{self.name} is already watching {symbol}.")
                return True

            stock, created = Stock.get_or_create(symbol=symbol, defaults={"name": name})
            if created:
                log.debug(f"{symbol} was added to watch for {self.name}.")

            StockToWatch.create(stock=stock, portfolio=self)
            log.debug(f"{self.name} started watching {symbol}.")
            return True
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to start watching {symbol} for portfolio {self.name}. {e}")
            return False

    def stop_watching(self, symbol):
        """
        Removes a stock from the watchlist for the current portfolio.

        Args:
            symbol (str): The symbol of the stock to stop watching (e.g., "AAPL").

        Returns:
            bool: True if the stock was successfully removed from the watchlist, False otherwise.
        """
        try:
            # Retrieve the Stock instance with the given symbol
            stock = Stock.get_or_none(Stock.symbol == symbol)
            if not stock:
                log.debug(f"Stock {symbol} not found.")
                return False
            # Delete the StockToWatch entry
            query = StockToWatch.delete().where(
                (StockToWatch.stock == stock) & (StockToWatch.portfolio == self)
            )
            rows_deleted = query.execute()
            if rows_deleted > 0:
                log.debug(f"Stock {symbol} successfully deleted from portfolio {self.name}.")
                return True
            log.debug(f"No stock {symbol} found in portfolio {self.name}.")
            return False
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to stop watching {symbol} for portfolio {self.name}. {e}")
            return False

    def get_watchlist(self):
        """
        Retrieves all stocks being watched for this portfolio.

        Returns:
            list[Stock]: A list of Stock objects associated with this portfolio. Returns an empty list if an error occurs.
        """
        try:
            return list(Stock.select().join(StockToWatch).where(StockToWatch.portfolio == self))
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to get watchlist for portfolio {self.name}. {e}")
            return []

    def deposit(self, external_id, amount, timestamp):
        """
        Deposits cash into the portfolio and records the transaction in the CashLedger.

        Args:
            external_id (int): An external identifier for the transaction.
            amount (float): The amount to deposit.
            timestamp (int): The timestamp of the transaction.

        Returns:
            bool: True if the deposit was successful, False otherwise.
        """
        try:
            with db.atomic():
                # Create a new entry in the CashLedger
                CashLedger.create(
                    external_id=external_id,
                    portfolio=self,
                    timestamp=timestamp,
                    amount=amount,
                    type=TransactionType.DEPOSIT.value,  # Store the enum value
                )

                # Update the portfolio's cash balance
                self.cash += amount
                self.save()

            log.info(f"DEPOSIT {amount} into portfolio {self.name}.")
            return True
        except Exception as e:
            log.error(f"Failed to deposit {amount} into portfolio {self.name}. {e}")
            return False

    def withdraw(self, external_id, amount, timestamp):
        """
        Withdraws cash from the portfolio and records the transaction in the CashLedger.

        Args:
            external_id (int): An external identifier for the transaction.
            amount (float): The amount to withdraw.
            timestamp (int): The timestamp of the transaction.

        Returns:
            bool: True if the withdrawal was successful, False otherwise.
        """
        try:
            with db.atomic():
                if amount > self.cash:
                    log.info(
                        f"Requested amount {amount} exceeds cash balance {self.cash} in portfolio {self.name}."
                    )
                    amount = self.cash  # Cap the amount to the available cash

                CashLedger.create(
                    external_id=external_id,
                    portfolio=self,
                    timestamp=timestamp,
                    amount=-amount,  # Negative amount to indicate withdrawal
                    type=TransactionType.WITHDRAW.value,
                )

                self.cash -= amount
                self.save()

            log.info(f"WITHDRAW {amount} from portfolio {self.name}.")
            return True
        except Exception as e:
            log.error(f"Failed to withdraw {amount} from portfolio {self.name}. {e}")
            return False


class StockToWatch(BaseModel):
    id = IntegerField(primary_key=True)
    stock = ForeignKeyField(Stock, field="id")
    portfolio = ForeignKeyField(Portfolio, field="id", on_delete="CASCADE")

    class Meta:
        table_name = "stock_to_watch"


class CashLedger(BaseModel):
    id = IntegerField(primary_key=True)
    external_id = TextField(unique=True)
    portfolio = ForeignKeyField(Portfolio, field="id", backref="cash_ledger")
    timestamp = IntegerField()
    amount = FloatField()
    type = TextField(choices=[TransactionType.DEPOSIT.name, TransactionType.WITHDRAW.name])

    class Meta:
        table_name = "cash_ledger"


"""
class OldPortfolio:
    def get_positions(self):
        return list(self.positions.keys())

    def get_position_size(self, symbol):
        symbol = symbol.upper()
        return 0 if symbol not in self.positions else self.positions[symbol]["size"]

    def sell(self, symbol, qty, price):
        symbol = symbol.upper()
        if self.get_position_size(symbol) == 0:
            log.error(f"Portfolio {self.name} has no position in {symbol}.")
            return False

        size = self.positions[symbol]["size"]

        if qty > size:
            log.info(
                f"Requested quantity {qty} is capped at {size} by {self.name}'s position size in {symbol}."
            )
            qty = size

        size -= qty

        if size == 0:
            self.positions.pop(symbol)
        else:
            self.positions[symbol]["size"] = size

        self.cash += qty * price
        log.info(f"SELL {qty} {symbol} @ {price}")

    def buy(self, symbol, qty, price):
        symbol = symbol.upper()

        if self.cash < qty * price:
            log.error(
                f"Cannot buy {qty} {symbol} at {price}. Portfolio {self.name} has {self.cash} in cash."
            )
            return False

        if self.get_position_size(symbol) == 0:
            self.positions[symbol] = {"size": 0, "average_price": 0.0}

        size = self.positions[symbol]["size"]
        average_price = self.positions[symbol]["average_price"]

        new_size = size + qty
        self.positions[symbol]["average_price"] = (average_price * size + price * qty) / new_size
        self.positions[symbol]["size"] = new_size
        self.cash -= qty * price
        log.info(f"BUY {qty} {symbol} @ {price}")

    def deposit_stock(self, symbol, qty, cost_basis_per_share, gain_loss=None):
        symbol = symbol.upper()

        if self.get_position_size(symbol) == 0:
            self.positions[symbol] = {"size": 0, "average_price": 0.0}

        size = self.positions[symbol]["size"]
        average_price = self.positions[symbol]["average_price"]

        new_size = size + qty
        self.positions[symbol]["average_price"] = (
            average_price * size + cost_basis_per_share * qty
        ) / new_size
        self.positions[symbol]["size"] = new_size

        gain_loss_as_string = f" Gain/Loss: {gain_loss}" if gain_loss else ""
        log.info(f"DEPOSIT_STOCK {qty} {symbol} @ {cost_basis_per_share}. {gain_loss_as_string}")

    def process_transactions(location):
        # a) Get last processed transactions batch. Batch name is epoch.
        # b) Load all the json files from the location with names more recent than last processed.
        # c) For each file
        # d) For each transaction dynamically invoke buy/sell/deposit/deposit_stock/withdraw
        # e) If stock not in stocks add there first
        # f) Inserts are idempotent
        # g) Respective methods will add an entry to the database for the transaction (not in eod position)
        # h) Once file completed update last processed batch for the location
        # i) Once all files are processed get all stock prices since last price in db
        #        (including symbols from transactions)
        # j) Update eod positions: if doesn't exist add, if exists update with delta
        #        (Assume that transactions will not be applied retroactively)
        # k) ...TODO
        pass

"""
