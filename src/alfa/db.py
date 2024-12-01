from enum import Enum

from peewee import (
    DateTimeField,
    FloatField,
    ForeignKeyField,
    IntegerField,
    Model,
    SqliteDatabase,
    TextField,
)

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
            if not isinstance(symbol, str) or not symbol.strip():
                raise ValueError("Symbol must be a non-empty string.")
            symbol = symbol.upper()

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
    timestamp = DateTimeField()  # Unix epoch time
    open = FloatField()
    high = FloatField()
    low = FloatField()
    close = FloatField()
    adjusted_close = FloatField()
    volume = IntegerField()


class CurrencyType(Enum):
    CAD = "CAD"
    USD = "USD"


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
        choices=[c.value for c in CurrencyType],
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
            portfolio = Portfolio.create(name=name, currency=currency.value)
            log.debug(f"Portfolio {name} in {currency.value} was successfully added.")
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

    def is_watching(self, symbol):
        """
        Determine whether the portfolio is currently watching a specific stock symbol.

        This method queries the `StockToWatch` table to check if there exists an association
        between the current portfolio (`self`) and the stock identified by the provided `symbol`.
        It returns `True` if such an association exists, indicating that the portfolio is
        actively watching the specified stock; otherwise, it returns `False`.

        Args:
            symbol (str): The stock symbol to check (e.g., "AAPL").

        Returns:
            bool:
                - `True` if the portfolio is watching the specified stock.
                - `False` otherwise.

        Raises:
            ValueError: If the `symbol` provided is an empty string or not a string type.
            peewee.OperationalError: If there is an issue connecting to the database.
            peewee.DatabaseError: For other general database-related errors.
        """
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("Symbol must be a non-empty string.")

        query = (
            StockToWatch.select()
            .join(Stock)
            .where((Stock.symbol == symbol) & (StockToWatch.portfolio == self))
        )
        return query.exists()

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
            if not isinstance(symbol, str) or not symbol.strip():
                raise ValueError("Symbol must be a non-empty string.")
            symbol = symbol.upper()

            if self.is_watching(symbol):
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
            if not isinstance(symbol, str) or not symbol.strip():
                raise ValueError("Symbol must be a non-empty string.")
            symbol = symbol.upper()

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

    def buy(self, external_id, timestamp, symbol, quantity, price, fees=0.0):
        """
        Buys a specified quantity of a stock, updates cash balance, and records the transaction.

        Args:
            external_id (int): Unique external identifier for the transaction.
            timestamp (int): Unix epoch time of the transaction.
            symbol (str): Stock symbol to buy.
            quantity (int): Number of shares to buy.
            price (float): Price per share.
            fees (float): Transaction fees.

        Returns:
            bool: True if the transaction was successful, False otherwise.
        """
        try:
            if not isinstance(symbol, str) or not symbol.strip():
                raise ValueError("Symbol must be a non-empty string.")
            symbol = symbol.upper()

            with db.atomic():
                total_cost = quantity * price + fees
                if self.cash < total_cost:
                    log.error(
                        f"Insufficient cash to buy {quantity} shares of {symbol}. \
                        Required: {total_cost}, Available: {self.cash}"
                    )
                    return False

                # Update cash balance
                self.cash -= total_cost
                self.save()

                # Automatically add symbol to watchlist
                if not self.start_watching(symbol):
                    return False
                stock = Stock.get(symbol=symbol)

                # TODO: update position

                # Record the transaction
                TransactionLedger.create(
                    external_id=external_id,
                    portfolio=self,
                    timestamp=timestamp,
                    stock=stock,
                    quantity=quantity,
                    price=price,
                    type=TransactionType.BUY.value,
                    fees=fees,
                )

            log.info(
                f"BUY {quantity} shares of {symbol} at {price} each. Total Cost: {total_cost}. Fees: {fees}."
            )
            return True

        except Exception as e:
            log.error(f"Failed to execute BUY {quantity} shares of {symbol} at {price} each. {e}")
            return False

    def deposit_in_kind(self, external_id, timestamp, symbol, quantity, cost_basis_per_share, fees=0.0):
        """
        Deposits a specified quantity of a stock into the portfolio, updates positions, and records the transaction.

        Args:
            external_id (int): Unique external identifier for the transaction.
            timestamp (int): Unix epoch time of the transaction.
            symbol (str): Stock symbol to deposit.
            quantity (int): Number of shares to deposit.
            cost_basis_per_share (float): Cost basis per share.
            fees (float): Transaction fees.

        Returns:
            bool: True if the transaction was successful, False otherwise.
        """
        try:
            if not isinstance(symbol, str) or not symbol.strip():
                raise ValueError("Symbol must be a non-empty string.")
            symbol = symbol.upper()

            with db.atomic():
                # Automatically add symbol to watchlist
                if not self.start_watching(symbol):
                    return False
                stock = Stock.get(symbol=symbol)

                # TODO: update position

                # Record the transaction
                TransactionLedger.create(
                    external_id=external_id,
                    portfolio=self,
                    timestamp=timestamp,
                    stock=stock,
                    quantity=quantity,
                    price=cost_basis_per_share,
                    type=TransactionType.DEPOSIT_STOCK.value,
                    fees=fees,
                )

            log.info(
                f"DEPOSIT_IN_KIND {quantity} shares of {symbol} at {cost_basis_per_share} each. Fees: {fees}."
            )
            return True

        except Exception as e:
            log.error(
                f"Failed to execute DEPOSIT_IN_KIND {quantity} shares of {symbol} at {cost_basis_per_share} each. {e}"
            )
            return False

    def sell(self, external_id, symbol, quantity, price, fees, timestamp):
        """
        Sells a specified quantity of a stock, updates cash balance, and records the transaction.

        Args:
            external_id (int): Unique external identifier for the transaction.
            symbol (str): Stock symbol to sell.
            quantity (int): Number of shares to sell.
            price (float): Price per share.
            fees (float): Transaction fees.
            timestamp (int): Unix epoch time of the transaction.

        Returns:
            bool: True if the transaction was successful, False otherwise.
        """
        try:
            if not isinstance(symbol, str) or not symbol.strip():
                raise ValueError("Symbol must be a non-empty string.")
            symbol = symbol.upper()

            with db.atomic():
                if not self.is_watching(symbol):
                    log.error(f"{self.name} is not owning stock {symbol.upper()}.")
                    return False
                stock = Stock.get(symbol=symbol)

                # TODO: update position and stop watching is liquidating sell

                # Calculate total proceeds
                total_proceeds = quantity * price - fees

                # Update cash balance
                self.cash += total_proceeds
                self.save()

                # Record the transaction
                TransactionLedger.create(
                    external_id=external_id,
                    portfolio=self,
                    timestamp=timestamp,
                    stock=stock,
                    quantity=-quantity,  # Negative quantity for SELL
                    price=price,
                    type=TransactionType.SELL.value,
                    fees=fees,
                )

            log.info(
                f"SELL {quantity} shares of {symbol.upper()} at {price} each. Total Proceeds: {total_proceeds}. Fees: {fees}."
            )
            return True

        except Exception as e:
            log.error(f"Failed to execute SELL {quantity} shares of {symbol.upper()} at {price} each. {e}")
            return False


class StockToWatch(BaseModel):
    id = IntegerField(primary_key=True)
    portfolio = ForeignKeyField(Portfolio, field="id", on_delete="CASCADE")
    stock = ForeignKeyField(Stock, field="id")

    class Meta:
        table_name = "stock_to_watch"
        indexes = ((("portfolio", "stock"), True),)


class CashLedger(BaseModel):
    id = IntegerField(primary_key=True)
    external_id = TextField(unique=True)
    portfolio = ForeignKeyField(Portfolio, field="id", backref="cash_ledger", on_delete="CASCADE")
    timestamp = IntegerField()  # Unix epoch time
    amount = FloatField()
    type = TextField(choices=[TransactionType.DEPOSIT.value, TransactionType.WITHDRAW.value])

    class Meta:
        table_name = "cash_ledger"
        indexes = ((("external_id",), True),)


class TransactionLedger(BaseModel):
    id = IntegerField(primary_key=True)
    external_id = TextField(unique=True)
    portfolio = ForeignKeyField(Portfolio, field="id", backref="transaction_ledger", on_delete="CASCADE")
    timestamp = IntegerField(null=False)  # Unix epoch time
    stock = ForeignKeyField(Stock, field="id")
    quantity = IntegerField()
    price = FloatField()
    type = TextField(
        choices=[[TransactionType.DEPOSIT.value, TransactionType.WITHDRAW.value]],
    )
    fees = FloatField()

    class Meta:
        table_name = "transaction_ledger"
        indexes = ((("external_id",), True),)


"""

CREATE TABLE IF NOT EXISTS transaction_ledger (
    id INTEGER PRIMARY KEY,
    external_id INTEGER NOT NULL UNIQUE,
    portfolio_id INTEGER,
    timestamp INTEGER NOT NULL,
    stock_id INTEGER,
    quantity NOT NULL,
    price NOT NULL,
    type NOT NULL, -- BUY, SELL, DEPOSIT_STOCK
    fees NOT NULL,
    FOREIGN KEY (portfolio_id) REFERENCES portfolio (id),
    FOREIGN KEY (stock_id) REFERENCES stock (id)
    );

CREATE TABLE IF NOT EXISTS last_processed_batch (
    location TEXT PRIMARY KEY,
    batch NOT NULL UNIQUE
    );

CREATE TABLE IF NOT EXISTS end_of_day_position (
    id INTEGER PRIMARY KEY,
    portfolio_id INTEGER,
    stock_id INTEGER,
    symbol TEXT NOT NULL UNIQUE,
    date NOT NULL,
    size NOT NULL,
    average_price NOT NULL,
    FOREIGN KEY (portfolio_id) REFERENCES portfolio (id),
    FOREIGN KEY (stock_id) REFERENCES stock (id)
    );


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
