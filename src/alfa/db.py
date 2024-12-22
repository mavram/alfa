import os
from datetime import datetime, time
from enum import Enum

from peewee import BigIntegerField, FloatField, ForeignKeyField, IntegerField, Model, SqliteDatabase, TextField

from alfa.config import log, settings

db = SqliteDatabase(None, pragmas={"foreign_keys": 1})


def _create_directories_for_path(path):
    # Extract the directory portion of the path
    directory = os.path.dirname(path)
    # Create directories if they are missing
    if directory:  # Avoid creating root directory if path is just a file name
        os.makedirs(directory, exist_ok=True)


def open_db():
    path = settings.DB_PATH

    log.debug(f"Initializing database at {path}.")
    _create_directories_for_path(path)
    db.init(path)
    return db


class BaseModel(Model):
    class Meta:
        database = db

    @staticmethod
    def get_models():
        return BaseModel.__subclasses__()


class IntervalType(Enum):
    DAY = "DAY"
    MINUTE = "MINUTE"
    SECOND = "SECOND"


def _as_timestamp_str(timestamp):
    if timestamp:
        timestamp = timestamp / 1000  # convert to seconds
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    return "None"


def _get_start_of_timestamp(timestamp, interval_type):
    if interval_type == IntervalType.DAY.value:
        # Convert milliseconds to seconds
        timestamp = timestamp / 1000
        # Convert to datetime object
        day = datetime.fromtimestamp(timestamp).date()
        start_timestamp = int(datetime.combine(day, time(0, 0, 0, 0)).timestamp() * 1000)
        # log.debug(
        #     f"timestamp:{_as_timestamp_str(timestamp)}. day: {day}. start_timestamp: {_as_timestamp_str(start_timestamp)}"
        # )
        return start_timestamp
    raise ValueError("Not implemented. {interval_type}.")


def _get_end_of_timestamp(timestamp, interval_type):
    if interval_type == IntervalType.DAY.value:
        # Convert milliseconds to seconds
        timestamp = timestamp / 1000
        # Convert to datetime object
        day = datetime.fromtimestamp(timestamp).date()
        end_timestamp = int(datetime.combine(day, time(23, 59, 59, 999000)).timestamp() * 1000)
        # log.debug(f"timestamp:{_as_timestamp_str(timestamp)}. day: {day}. end_timestamp: {_as_timestamp_str(end_timestamp)}")
        return end_timestamp
    raise ValueError("Not implemented. {interval_type}.")


class Stock(BaseModel):
    id = IntegerField(primary_key=True)
    symbol = TextField(unique=True)
    name = TextField(null=True)

    def get_price(self, end_timestamp=None, interval_type=IntervalType.DAY.value):
        try:
            where_clause = True
            time_interval = "Without time interval constraints."
            if end_timestamp:
                start_timestamp = _get_start_of_timestamp(end_timestamp, interval_type)
                where_clause = (Price.timestamp >= start_timestamp) & (Price.timestamp <= end_timestamp)
                time_interval = f"Between {_as_timestamp_str(start_timestamp)} and {_as_timestamp_str(end_timestamp)}."
            price = self.prices.where(where_clause).order_by(Price.timestamp.desc()).first()
            if price:
                log.debug(
                    f"{self.symbol}'s most recent price is from {_as_timestamp_str(price.timestamp)}. "
                    f"{price.adjusted_close:.2f}"
                )
            else:
                log.debug(f"{self.symbol} has no prices. {time_interval}")
            return price
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to get the price for {self.symbol}: {type(e).__name__} : {e}")
            raise e

    def add_price(self, timestamp, open, high, low, close, adjusted_close, volume):
        try:
            if volume < 0:
                raise ValueError("Volume cannot be negative.")

            log.debug(f"Adding price for {self.symbol} on {_as_timestamp_str(timestamp)}.")

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
            log.debug(f"Added price for {self.symbol} on {_as_timestamp_str(timestamp)} successfully.")
            return price
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to add price for {self.symbol}: {type(e).__name__} : {e}")
            raise e


class Price(BaseModel):
    id = IntegerField(primary_key=True)
    stock = ForeignKeyField(Stock, backref="prices", on_delete="CASCADE")
    symbol = TextField()
    timestamp = BigIntegerField()  # Unix epoch time
    open = FloatField()
    high = FloatField()
    low = FloatField()
    close = FloatField()
    adjusted_close = FloatField()
    volume = IntegerField()

    class Meta:
        table_name = "price"
        indexes = ((("stock", "timestamp"), True),)  # Unique constraint on stock and timestamp


class CurrencyType(Enum):
    CAD = "CAD"
    USD = "USD"


class TransactionType(str, Enum):
    BUY = "BUY"
    DEPOSIT = "DEPOSIT"
    DEPOSIT_IN_KIND = "DEPOSIT_IN_KIND"
    SELL = "SELL"
    WITHDRAW = "WITHDRAW"


def _as_validated_symbol(symbol):
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("Symbol must be a non-empty string.")
    return symbol.upper()


class Portfolio(BaseModel):
    id = IntegerField(primary_key=True)
    name = TextField(unique=True)
    currency = TextField(choices=[c.value for c in CurrencyType])

    @staticmethod
    def initialize(name, currency=CurrencyType.USD):
        try:
            portfolio, created = Portfolio.get_or_create(name=name, defaults={"currency": currency.value})
            if created:
                log.debug(f"Created portfolio {name} using currency {currency.value}.")
            return portfolio
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to add portfolio {name}: {type(e).__name__} : {e}")
            raise e

    @staticmethod
    def get_portfolios():
        try:
            return list(Portfolio.select())
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to retrieve portfolios: {e}")
            raise e

    def is_watching(self, symbol):
        try:
            symbol = _as_validated_symbol(symbol)

            query = StockToWatch.select().join(Stock).where((Stock.symbol == symbol) & (StockToWatch.portfolio == self))
            return query.exists()
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to check watchlist for {symbol} in portfolio {self.name}: {type(e).__name__} : {e}")
            raise e

    def start_watching(self, symbol, name=None):
        try:
            symbol = _as_validated_symbol(symbol)

            stock, created = Stock.get_or_create(symbol=symbol, defaults={"name": name})
            if created:
                log.debug(f"Portfolio {self.name} added new stock {symbol}.")

            if self.is_watching(symbol):
                log.debug(f"Portfolio {self.name} is already watching {symbol}.")
                return stock

            StockToWatch.create(stock=stock, portfolio=self)
            log.debug(f"Portfolio {self.name} started watching {symbol}.")

            return stock
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to add {symbol} to watchlist in portfolio {self.name}: {type(e).__name__} : {e}")
            raise e

    def stop_watching(self, symbol):
        try:
            symbol = _as_validated_symbol(symbol)

            if not self.is_watching(symbol):
                log.debug(f"Portfolio {self.name} is not watching {symbol}.")
                return

            position = self.get_position(symbol)
            if position:
                log.debug(f"Cannot remove {symbol} from watchlist in portfolio {self.name} due to active position.")
                return

            stock = Stock.get_or_none(Stock.symbol == symbol)
            rows_deleted = (
                StockToWatch.delete().where((StockToWatch.stock == stock) & (StockToWatch.portfolio == self)).execute()
            )
            if rows_deleted > 0:
                log.debug(f"Removed {symbol} from watchlist in portfolio {self.name}.")
            else:  # pragma: no cover
                log.debug(f"No watchlist entry found for {symbol} in portfolio {self.name}.")
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to remove {symbol} from watchlist in portfolio {self.name}: {type(e).__name__} : {e}")
            raise e

    def get_watchlist(self):
        try:
            return list(Stock.select().join(StockToWatch).where(StockToWatch.portfolio == self))
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to retrieve watchlist for portfolio {self.name}: {type(e).__name__} : {e}")
            raise e

    def get_cash(self, end_timestamp=None, interval_type=IntervalType.DAY.value):
        try:
            where_clause = True
            if end_timestamp:
                where_clause = Balance.timestamp <= end_timestamp
            balance = self.balances.where(where_clause).order_by(Balance.timestamp.desc()).first()
            if balance:
                log.debug(
                    f"Portfolio {self.name}'s most recent cash balance is from {_as_timestamp_str(balance.timestamp)}. "
                    f"Cash: {balance.cash:.2f}."
                )
                return balance.cash

            log.debug(f"Portfolio {self.name} has no balances.")
            return 0.0
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to get cash balance for portfolio {self.name}: {type(e).__name__} : {e}")
            raise e

    def _update_balance(self, timestamp, amount):
        try:
            log.debug(f"Updating cash balance in portfolio {self.name} at {_as_timestamp_str(timestamp)} with {amount}.")

            current_balance = self.get_cash()
            new_balance = current_balance + amount
            if new_balance < 0:
                raise ValueError(f"Insufficient funds in portfolio {self.name} to update by {amount:.2f} amount.")

            Balance.create(portfolio=self, timestamp=timestamp, cash=new_balance)

            log.debug(
                f"Updated cash balance in portfolio {self.name}: "
                f"Previous Balance={current_balance:.2f}. New Balance={new_balance:.2f}"
            )
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to update cash balance in portfolio {self.name}: {type(e).__name__} : {e}")
            raise e

    def get_position(self, symbol, end_timestamp=None, interval_type=IntervalType.DAY.value):
        try:
            symbol = _as_validated_symbol(symbol)
            stock = Stock.get_or_none(Stock.symbol == symbol)
            if not stock:
                log.debug(f"Stock {symbol} does not exist in the database.")
                return None
            where_clause = Position.stock == stock
            if end_timestamp:
                where_clause &= Position.timestamp <= end_timestamp
            position = self.positions.where(where_clause).order_by(Position.timestamp.desc()).first()
            if position:
                # Fetch the latest price up to the specified timestamp
                latest_price = stock.get_price(end_timestamp)
                if latest_price:
                    position.market_price = latest_price.adjusted_close
                    log.debug(
                        f"Updated market price for {symbol} to {position.market_price:.2f} "
                        f"based on price from {_as_timestamp_str(latest_price.timestamp)}."
                    )
                else:
                    # Handle the case where no price is available
                    log.debug(f"No available market price for {symbol}.")

                log.debug(
                    f"Portfolio {self.name}'s most recent {symbol} position is from {_as_timestamp_str(position.timestamp)}."
                    f"Size:{position.size}. "
                    f"Average Price:{position.average_price:.2f}. "
                    f"Market Price:{position.market_price:.2f}"
                )
                if position.size > 0.0:
                    return position
            log.debug(f"Portfolio {self.name} has no position in {symbol}.")
            return None
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to get position for {symbol} in portfolio {self.name}: {type(e).__name__} : {e}")
            raise e

    def _update_position(self, timestamp, symbol, quantity, price):
        try:
            symbol = _as_validated_symbol(symbol)
            stock = Stock.get_or_none(Stock.symbol == symbol)
            if not stock:
                raise ValueError(f"Stock {symbol} does not exist in the database.")

            log.debug(
                f"Updating portfolio {self.name}'s {symbol} position at {_as_timestamp_str(timestamp)} "
                f"with {quantity} shares at {price:.2f} each."
            )

            position = self.get_position(symbol)

            current_size = position.size if position else 0.0
            current_average_price = position.average_price if position else 0.0

            new_size = current_size + quantity
            if new_size < 0:
                raise ValueError(f"Cannot remove {abs(quantity)} shares from {symbol}; only {current_size} available.")

            if new_size == 0:
                log.debug(f"Liquidating position for {symbol} in portfolio {self.name}.")
                new_average_price = 0.0
                new_market_price = 0.0
            else:
                new_average_price = current_average_price
                new_market_price = price
                if quantity > 0:
                    total_cost = (current_average_price * current_size) + (price * quantity)
                    new_average_price = total_cost / new_size

            new_position = Position.create(
                portfolio=self,
                stock=stock,
                timestamp=timestamp,
                size=new_size,
                average_price=new_average_price,
                market_price=new_market_price,
            )

            log.debug(
                f"Updated portfolio {self.name}'s {symbol} position: "
                f"Size={new_position.size}, Average Price={new_position.average_price:.2f}. "
                f"Market Price={new_position.market_price:.2f}."
            )

            return new_position
        except Exception as e:  # pragma: no covers
            log.error(f"Failed to create position for {symbol} in portfolio {self.name}: {type(e).__name__} : {e}")
            raise e

    def _update_cash_ledger(self, external_id, timestamp, type, fees, amount):
        # Record Cash Transaction
        CashLedger.create(
            external_id=external_id,
            portfolio=self,
            timestamp=timestamp,
            amount=amount,
            type=type,
            fees=fees,
        )

    def _update_transaction_ledger(self, external_id, timestamp, type, symbol, fees, quantity, price):
        # Record Transaction
        stock = Stock.get(Stock.symbol == symbol)
        TransactionLedger.create(
            external_id=external_id,
            portfolio=self,
            timestamp=timestamp,
            stock=stock,
            quantity=quantity,
            price=price,
            type=type,
            fees=fees,
        )

    def deposit(self, external_id, timestamp, amount, fees=0.0):
        try:
            log.info(f"Depositing {amount} into portfolio {self.name}.")
            with db.atomic():
                self._update_cash_ledger(external_id, timestamp, TransactionType.DEPOSIT.value, fees, amount)
                total_amount_to_deposit = amount - fees
                self._update_balance(timestamp, total_amount_to_deposit)

            log.info(f"Deposited {amount} into portfolio {self.name}.")
            return self
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to deposit {amount} into portfolio {self.name}: {type(e).__name__} : {e}")
            raise e

    def withdraw(self, external_id, timestamp, amount, fees=0.0):
        try:
            log.info(f"Withdrawing {amount} from portfolio {self.name}.")

            with db.atomic():
                total_amount_to_withdraw = amount + fees
                current_balance = self.get_cash()
                if total_amount_to_withdraw > current_balance:
                    raise ValueError(
                        f"Withdrawal amount {amount} and fees {fees} "
                        f"exceeds available cash {current_balance} in portfolio {self.name}."
                    )

                self._update_cash_ledger(external_id, timestamp, TransactionType.WITHDRAW.value, fees, amount)
                self._update_balance(timestamp, -total_amount_to_withdraw)

            log.info(f"Withdrew {amount} from portfolio {self.name}.")
            return self
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to withdraw {amount} from portfolio {self.name}: {type(e).__name__} : {e}")
            raise e

    def buy(self, external_id, timestamp, symbol, quantity, price, fees=0.0):
        try:
            log.info(f"Buying {quantity} shares of {symbol} at ${price:.2f} each in portfolio {self.name}.")

            symbol = _as_validated_symbol(symbol)

            with db.atomic():
                total_cost = quantity * price + fees
                current_balance = self.get_cash()
                if current_balance < total_cost:
                    log.error(
                        f"Insufficient cash to buy {quantity} shares of {symbol}. "
                        f"Required: {total_cost}. Available: {current_balance}."
                    )
                    raise ValueError(
                        f"Portfolio {self.name} does not have sufficient cash to buy {quantity} shares of {symbol}."
                    )

                # Add symbol to watchlist
                self.start_watching(symbol)
                self._update_transaction_ledger(
                    external_id, timestamp, TransactionType.BUY.value, symbol, fees, quantity, price
                )
                # Update cash balance
                self._update_balance(timestamp, -total_cost)
                # Update position
                self._update_position(timestamp, symbol, quantity, price)

            log.info(
                f"Bought {quantity} shares of {symbol} at ${price:.2f} each. "
                f"Total Cost: ${total_cost:.2f}. Fees: ${fees:.2f}."
            )
            return self
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to buy {quantity} shares of {symbol} at ${price:.2f}: {type(e).__name__} : {e}")
            raise e

    def deposit_in_kind(self, external_id, timestamp, symbol, quantity, cost_basis_per_share, fees=0.0):
        try:
            log.info(f"Depositing {quantity} shares of {symbol} at ${cost_basis_per_share:.2f} each in {self.name}.")

            symbol = _as_validated_symbol(symbol)

            with db.atomic():
                total_fees = fees
                current_balance = self.get_cash()
                if current_balance < total_fees:
                    log.error(
                        f"Insufficient cash to cover fees for depositing {quantity} shares of {symbol}. "
                        f"Required Fees: ${total_fees:.2f}. Available Cash: ${current_balance:.2f}."
                    )
                    raise ValueError(
                        f"Portfolio {self.name} does not have sufficient cash to cover fees "
                        f"for depositing {quantity} shares of {symbol}."
                    )

                self._update_transaction_ledger(
                    external_id, timestamp, TransactionType.DEPOSIT_IN_KIND.value, symbol, fees, quantity, cost_basis_per_share
                )
                # Update cash balance to cover fees
                if total_fees > 0:
                    self._update_balance(timestamp, -total_fees)
                # Add symbol to watchlist
                self.start_watching(symbol)
                # Update position
                self._update_position(timestamp, symbol, quantity, cost_basis_per_share)

            log.info(f"Deposited {quantity} shares of {symbol} at ${cost_basis_per_share:.2f} each. " f"Fees: ${fees:.2f}.")
            return self
        except Exception as e:  # pragma: no cover
            log.error(
                f"Failed to deposit {quantity} shares of {symbol} at ${cost_basis_per_share:.2f}: {type(e).__name__} : {e}"
            )
            raise e

    def sell(self, external_id, timestamp, symbol, quantity, price, fees=0.0):
        try:
            log.info(f"Selling {quantity} shares of {symbol} at ${price:.2f} each in {self.name}.")

            symbol = _as_validated_symbol(symbol)

            with db.atomic():
                position = self.get_position(symbol)
                if not position:
                    log.error(f"Portfolio {self.name} has no position in {symbol}.")
                    raise ValueError(f"No active position in {symbol} to sell.")

                if quantity > position.size:
                    raise ValueError(
                        f"Request to sell {quantity} shares of {symbol} exceeds current position of {position.size} shares."
                    )

                self._update_transaction_ledger(
                    external_id, timestamp, TransactionType.SELL.value, symbol, fees, quantity, price
                )

                total_proceeds = quantity * price - fees
                # Update cash balance
                self._update_balance(timestamp, total_proceeds)
                # Update position
                position = self._update_position(timestamp, symbol, -quantity, price)
                if position.size == 0.0:
                    # Position was liquidated, stop watching
                    self.stop_watching(symbol)

            log.info(
                f"Sold {quantity} shares of {symbol} at ${price:.2f} each. "
                f"Total Proceeds: ${total_proceeds:.2f}. Fees: ${fees:.2f}."
            )
            return self
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to sell {quantity} shares of {symbol} at ${price:.2f}: {type(e).__name__} : {e}")
            raise e

    def get_eod_balance(self, timestamp=None):
        if not timestamp:
            timestamp = int(datetime.now().timestamp() * 1000)
        day = datetime.fromtimestamp(timestamp / 1000).date()
        end_timestamp = _get_end_of_timestamp(timestamp, IntervalType.DAY.value)

        try:
            cash = self.get_cash(end_timestamp, IntervalType.DAY.value)
            log.debug(f"Portfolio {self.name}'s {day} end of day balance is {cash:.2f}.")
            return cash
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to retrieve {day} end of day balance for {self.name}: {type(e).__name__} : {e}")
            raise e

    def get_eod_position(self, symbol, timestamp=None):
        if not timestamp:
            timestamp = int(datetime.now().timestamp() * 1000)
        day = datetime.fromtimestamp(timestamp / 1000).date()
        end_timestamp = _get_end_of_timestamp(timestamp, IntervalType.DAY.value)

        try:
            symbol = _as_validated_symbol(symbol)
            position = self.get_position(symbol, end_timestamp, IntervalType.DAY.value)
            if position:
                log.debug(
                    f"Portfolio {self.name}'s {day} end of day position for {symbol}, "
                    f"as of {_as_timestamp_str(position.timestamp)}, is {position.size} shares."
                    f"Average Price: {position.average_price:.2f}. Market Price: {position.market_price:.2f}."
                )
            else:
                log.debug(f"Portfolio {self.name} has no {day} end of day positions for {symbol}.")
            return position
        except Exception as e:  # pragma: no cover
            log.error(
                f"Failed to retrieve {day} end of day position for {symbol} in portfolio {self.name}: {type(e).__name__} : {e}"
            )
            raise e


class StockToWatch(BaseModel):
    id = IntegerField(primary_key=True)
    portfolio = ForeignKeyField(Portfolio, backref="watchlist", on_delete="CASCADE")
    stock = ForeignKeyField(Stock, on_delete="CASCADE")

    class Meta:
        table_name = "stock_to_watch"
        indexes = ((("portfolio", "stock"), True),)  # Unique constraint on portfolio and stock


class CashLedger(BaseModel):
    id = IntegerField(primary_key=True)
    external_id = TextField(unique=True)
    portfolio = ForeignKeyField(Portfolio, backref="deposits_and_withdraws", on_delete="CASCADE")
    timestamp = BigIntegerField()  # Unix epoch time
    amount = FloatField()
    type = TextField(choices=[TransactionType.DEPOSIT, TransactionType.WITHDRAW])
    fees = FloatField()

    class Meta:
        table_name = "cash_ledger"
        indexes = ((("external_id",), True),)


class TransactionLedger(BaseModel):
    id = IntegerField(primary_key=True)
    external_id = TextField(unique=True)
    portfolio = ForeignKeyField(Portfolio, backref="transactions", on_delete="CASCADE")
    timestamp = BigIntegerField(null=False)  # Unix epoch time
    stock = ForeignKeyField(Stock, on_delete="CASCADE")
    quantity = IntegerField()
    price = FloatField()
    type = TextField(
        choices=[
            TransactionType.BUY,
            TransactionType.SELL,
            TransactionType.DEPOSIT_IN_KIND,
        ]
    )
    fees = FloatField()

    class Meta:
        table_name = "transaction_ledger"
        indexes = ((("external_id",), True),)


class Position(BaseModel):
    id = IntegerField(primary_key=True)
    timestamp = BigIntegerField(null=False)  # Unix epoch time
    portfolio = ForeignKeyField(Portfolio, backref="positions", on_delete="CASCADE")
    stock = ForeignKeyField(Stock, on_delete="CASCADE")
    size = IntegerField()
    average_price = FloatField()
    market_price = FloatField()

    class Meta:
        table_name = "position"
        indexes = ((("portfolio", "stock", "timestamp"), True),)  # Unique constraint on portfolio, timestamp, and stock


class Balance(BaseModel):
    id = IntegerField(primary_key=True)
    timestamp = BigIntegerField(null=False)  # Unix epoch time
    portfolio = ForeignKeyField(Portfolio, backref="balances", on_delete="CASCADE")
    cash = FloatField(default=0.0)

    class Meta:
        table_name = "balance"
        indexes = ((("portfolio", "timestamp"), True),)  # Unique constraint on portfolio and timestamp


"""
[ ] import transactions (deposit, withdraw, buy, sell, ...) from files
"""
