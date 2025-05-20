import logging
import os
from datetime import datetime, time
from enum import Enum

from peewee import BigIntegerField, FloatField, ForeignKeyField, IntegerField, Model, SqliteDatabase, TextField

log = logging.getLogger("alfa")
logging.getLogger("peewee").setLevel(max(log.getEffectiveLevel(), logging.ERROR))


db = SqliteDatabase(None, pragmas={"foreign_keys": 1})


def open_db(path):
    log.debug(f"Initializing database at {path}.")
    # Extract the directory portion of the path
    directory = os.path.dirname(path)
    # Create directories if they are missing
    if directory:  # Avoid creating root directory if path is just a file name
        os.makedirs(directory, exist_ok=True)
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


def strtimestamp(timestamp):
    if not timestamp:
        return None
    timestamp = timestamp / 1000  # convert to seconds
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def get_eod_timestamp(day):
    if not day:
        day = datetime.now().date()
    return int(datetime.combine(day, time.max).timestamp() * 1000)


class Stock(BaseModel):
    id = IntegerField(primary_key=True)
    symbol = TextField(unique=True)
    name = TextField(null=True)

    def get_price(self, to_timestamp=None, interval_type=IntervalType.DAY.value):
        def _get_from_for_to(to_timestamp, interval_type):
            if interval_type == IntervalType.DAY.value:
                # Convert milliseconds to seconds
                to_timestamp = to_timestamp / 1000
                # Convert to datetime object
                day = datetime.fromtimestamp(to_timestamp).date()
                from_timestamp = int(datetime.combine(day, time.min).timestamp() * 1000)
                return from_timestamp
            raise ValueError("Not implemented. {interval_type}.")

        try:
            where_clause = True
            from_and_to_str = "Without from and to constraints."
            if to_timestamp:
                from_timestamp = _get_from_for_to(to_timestamp, interval_type)
                where_clause = (Price.timestamp >= from_timestamp) & (Price.timestamp <= to_timestamp)
                from_and_to_str = f"From {strtimestamp(from_timestamp)} to {strtimestamp(to_timestamp)}."
            price = self.prices.where(where_clause).order_by(Price.timestamp.desc()).first()
            if price:
                log.debug(
                    f"{self.symbol}'s most recent price is from {strtimestamp(price.timestamp)}. "
                    f"{price.adjusted_close:.2f}, {from_and_to_str}"
                )
            else:
                log.debug(f"{self.symbol} has no prices. {from_and_to_str}")
            return price
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to get the price for {self.symbol}: {type(e).__name__} : {e}")
            raise e

    def add_price(self, timestamp, open, high, low, close, adjusted_close, volume):
        try:
            if volume < 0:
                raise ValueError("Volume cannot be negative.")

            log.debug(f"Adding price for {self.symbol} on {strtimestamp(timestamp)}.")

            # TODO: switch to get_or_create
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
            log.debug(f"Added price for {self.symbol} on {strtimestamp(timestamp)} successfully.")
            return price
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to add price for {self.symbol}: {type(e).__name__} : {e}")
            raise e

    def get_eod_price(self, day=None):
        to_timestamp = get_eod_timestamp(day)
        return self.get_price(to_timestamp, IntervalType.DAY.value)


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

    @staticmethod
    def init(name):
        try:
            portfolio, created = Portfolio.get_or_create(name=name)
            if created:
                log.debug(f"Created portfolio {name}.")
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

    def add_account(self, name, currency=CurrencyType.USD):
        try:
            # TODO: validate inputs

            log.debug(f"Adding account {name} in {currency} to portfolio {self.name}.")

            # TODO: switch to get_or_create
            account = Account.create(
                portfolio=self,
                name=name,
                currency=currency.value,
            )
            log.debug(f"Adding account {name} to portfolio {self.name}.")
            return account
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to add account {name}: {type(e).__name__} : {e}")
            raise e

    def get_accounts(self):
        return self.accounts

    def get_account(self, name, currency):
        try:
            # TODO: validate inputs

            account = Account.get_or_none(
                (Account.portfolio == self) & (Account.name == name) & (Account.currency == currency.value)
            )

            return account
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to get account {name} in {currency}: {type(e).__name__} : {e}")
            raise e


class StockToWatch(BaseModel):
    id = IntegerField(primary_key=True)
    portfolio = ForeignKeyField(Portfolio, backref="watchlist", on_delete="CASCADE")
    stock = ForeignKeyField(Stock, on_delete="CASCADE")

    class Meta:
        table_name = "stock_to_watch"
        indexes = ((("portfolio", "stock"), True),)  # Unique constraint on portfolio and stock


class Account(BaseModel):
    id = IntegerField(primary_key=True)
    portfolio = ForeignKeyField(Portfolio, backref="accounts", on_delete="CASCADE")
    name = TextField()
    currency = TextField(choices=[c.value for c in CurrencyType])

    class Meta:
        table_name = "account"
        indexes = (
            (
                ("portfolio", "name", "currency"),
                True,
            ),
        )  # Unique constraint on portfolio, name, and currency

    def get_cash(self, to_timestamp=None):
        try:
            where_clause = True
            if to_timestamp:
                where_clause = Balance.timestamp <= to_timestamp
            balance = self.balances.where(where_clause).order_by(Balance.timestamp.desc()).first()
            if balance:
                log.debug(
                    f"Account {self.name}'s most recent cash balance is from {strtimestamp(balance.timestamp)}. "
                    f"Cash: {balance.cash:.2f}."
                )
                return balance.cash

            log.debug(f"Account {self.name} has no balances.")
            return 0.0
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to get cash balance for account {self.name}: {type(e).__name__} : {e}")
            raise e

    def update_balance(self, timestamp, amount):
        try:
            log.debug(f"Updating cash balance in account {self.name} at {strtimestamp(timestamp)} with {amount}.")

            current_balance = self.get_cash()
            new_balance = current_balance + amount
            if new_balance < 0:
                raise ValueError(f"Insufficient funds in account {self.name} to update by {amount:.2f} amount.")

            Balance.create(account=self, timestamp=timestamp, cash=new_balance)

            log.debug(
                f"Updated cash balance in account {self.name}: "
                f"Previous Balance={current_balance:.2f}. New Balance={new_balance:.2f}"
            )
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to update cash balance in account {self.name}: {type(e).__name__} : {e}")
            raise e

    def get_position(self, symbol, to_timestamp=None):
        try:
            symbol = _as_validated_symbol(symbol)
            stock = Stock.get_or_none(Stock.symbol == symbol)
            if not stock:
                log.debug(f"Stock {symbol} does not exist in the database.")
                return None
            where_clause = Position.stock == stock
            if to_timestamp:
                where_clause &= Position.timestamp <= to_timestamp
            position = self.positions.where(where_clause).order_by(Position.timestamp.desc()).first()
            if position:
                # Fetch the latest price up to the specified timestamp
                latest_price = stock.get_price(to_timestamp)
                if latest_price:
                    position.market_price = latest_price.adjusted_close
                    log.debug(
                        f"Updated market price for {symbol} to {position.market_price:.2f} "
                        f"based on price from {strtimestamp(latest_price.timestamp)}."
                    )
                else:
                    # Handle the case where no price is available
                    log.debug(f"No available market price for {symbol}.")

                log.debug(
                    f"Account {self.name}'s most recent {symbol} position is from {strtimestamp(position.timestamp)}."
                    f"Size:{position.size}. "
                    f"Average Price:{position.average_price:.2f}. "
                    f"Market Price:{position.market_price:.2f}"
                )
                if position.size > 0.0:
                    return position
            log.debug(f"Account {self.name} has no position in {symbol}.")
            return None
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to get position for {symbol} in account {self.name}: {type(e).__name__} : {e}")
            raise e

    def update_position(self, timestamp, symbol, quantity, price):
        try:
            symbol = _as_validated_symbol(symbol)
            stock = Stock.get_or_none(Stock.symbol == symbol)
            if not stock:
                raise ValueError(f"Stock {symbol} does not exist in the database.")

            log.debug(
                f"Updating account {self.name}'s {symbol} position at {strtimestamp(timestamp)} "
                f"with {quantity} shares at {price:.2f} each."
            )

            position = self.get_position(symbol)

            current_size = position.size if position else 0.0
            current_average_price = position.average_price if position else 0.0

            new_size = current_size + quantity
            if new_size < 0:
                raise ValueError(f"Cannot remove {abs(quantity)} shares from {symbol}; only {current_size} available.")

            if new_size == 0:
                log.debug(f"Liquidating position for {symbol} in account {self.name}.")
                new_average_price = 0.0
                new_market_price = 0.0
            else:
                new_average_price = current_average_price
                new_market_price = price
                if quantity > 0:
                    total_cost = (current_average_price * current_size) + (price * quantity)
                    new_average_price = total_cost / new_size

            new_position = Position.create(
                account=self,
                stock=stock,
                timestamp=timestamp,
                size=new_size,
                average_price=new_average_price,
                market_price=new_market_price,
            )

            log.debug(
                f"Updated account {self.name}'s {symbol} position: "
                f"Size={new_position.size}, Average Price={new_position.average_price:.2f}. "
                f"Market Price={new_position.market_price:.2f}."
            )

            return new_position
        except Exception as e:  # pragma: no covers
            log.error(f"Failed to create position for {symbol} in account {self.name}: {type(e).__name__} : {e}")
            raise e

    def update_cash_ledger(self, external_id, timestamp, type, fees, amount):
        # Record Cash Transaction
        CashLedger.create(
            external_id=external_id,
            account=self,
            timestamp=timestamp,
            amount=amount,
            type=type,
            fees=fees,
        )

    def update_transaction_ledger(self, external_id, timestamp, type, symbol, fees, quantity, price):
        # Record Transaction
        stock = Stock.get(Stock.symbol == symbol)
        TransactionLedger.create(
            external_id=external_id,
            account=self,
            timestamp=timestamp,
            stock=stock,
            quantity=quantity,
            price=price,
            type=type,
            fees=fees,
        )

    def deposit(self, external_id, timestamp, amount, fees=0.0):
        try:
            log.info(f"Depositing {amount} into account {self.name}.")
            with db.atomic():
                self.update_cash_ledger(external_id, timestamp, TransactionType.DEPOSIT.value, fees, amount)
                total_amount_to_deposit = amount - fees
                self.update_balance(timestamp, total_amount_to_deposit)

            log.info(f"Deposited {amount} into account {self.name}.")
            return self
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to deposit {amount} into account {self.name}: {type(e).__name__} : {e}")
            raise e

    def withdraw(self, external_id, timestamp, amount, fees=0.0):
        try:
            log.info(f"Withdrawing {amount} from account {self.name}.")

            with db.atomic():
                total_amount_to_withdraw = amount + fees
                current_balance = self.get_cash()
                if total_amount_to_withdraw > current_balance:
                    raise ValueError(
                        f"Withdrawal amount {amount} and fees {fees} "
                        f"exceeds available cash {current_balance} in account {self.name}."
                    )

                self.update_cash_ledger(external_id, timestamp, TransactionType.WITHDRAW.value, fees, amount)
                self.update_balance(timestamp, -total_amount_to_withdraw)

            log.info(f"Withdrew {amount} from account {self.name}.")
            return self
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to withdraw {amount} from account {self.name}: {type(e).__name__} : {e}")
            raise e

    def buy(self, external_id, timestamp, symbol, quantity, price, fees=0.0):
        try:
            log.info(f"Buying {quantity} shares of {symbol} at ${price:.2f} each in account {self.name}.")

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
                        f"Account {self.name} does not have sufficient cash to buy {quantity} shares of {symbol}."
                    )

                # Add symbol to watchlist
                self.portfolio.start_watching(symbol)
                self.update_transaction_ledger(
                    external_id, timestamp, TransactionType.BUY.value, symbol, fees, quantity, price
                )
                # Update cash balance
                self.update_balance(timestamp, -total_cost)
                # Update position
                self.update_position(timestamp, symbol, quantity, price)

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
                        f"Account {self.name} does not have sufficient cash to cover fees "
                        f"for depositing {quantity} shares of {symbol}."
                    )

                self.update_transaction_ledger(
                    external_id, timestamp, TransactionType.DEPOSIT_IN_KIND.value, symbol, fees, quantity, cost_basis_per_share
                )
                # Update cash balance to cover fees
                if total_fees > 0:
                    self.update_balance(timestamp, -total_fees)
                # Add symbol to watchlist
                self.portfolio.start_watching(symbol)
                # Update position
                self.update_position(timestamp, symbol, quantity, cost_basis_per_share)

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
                    log.error(f"Account {self.name} has no position in {symbol}.")
                    raise ValueError(f"No active position in {symbol} to sell.")

                if quantity > position.size:
                    raise ValueError(
                        f"Request to sell {quantity} shares of {symbol} exceeds current position of {position.size} shares."
                    )

                self.update_transaction_ledger(
                    external_id, timestamp, TransactionType.SELL.value, symbol, fees, quantity, price
                )

                total_proceeds = quantity * price - fees
                # Update cash balance
                self.update_balance(timestamp, total_proceeds)
                # Update position
                position = self.update_position(timestamp, symbol, -quantity, price)
                if position.size == 0.0:
                    # Position was liquidated, stop watching
                    self.portoflio.stop_watching(symbol)

            log.info(
                f"Sold {quantity} shares of {symbol} at ${price:.2f} each. "
                f"Total Proceeds: ${total_proceeds:.2f}. Fees: ${fees:.2f}."
            )
            return self
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to sell {quantity} shares of {symbol} at ${price:.2f}: {type(e).__name__} : {e}")
            raise e

    def get_eod_balance(self, day=None):
        to_timestamp = get_eod_timestamp(day)
        day = datetime.fromtimestamp(to_timestamp / 1000).date()

        try:
            cash = self.get_cash(to_timestamp)
            log.debug(f"Account {self.name}'s {day} end of day balance is {cash:.2f}.")
            return cash
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to retrieve {day} end of day balance for {self.name}: {type(e).__name__} : {e}")
            raise e

    def get_eod_position(self, symbol, day=None):
        to_timestamp = get_eod_timestamp(day)
        day = datetime.fromtimestamp(to_timestamp / 1000).date()

        try:
            symbol = _as_validated_symbol(symbol)
            position = self.get_position(symbol, to_timestamp)
            if position:
                log.debug(
                    f"Account {self.name}'s {day} end of day position for {symbol}, "
                    f"as of {strtimestamp(position.timestamp)}, is {position.size} shares."
                    f"Average Price: {position.average_price:.2f}. Market Price: {position.market_price:.2f}."
                )
            else:
                log.debug(f"Account {self.name} has no {day} end of day positions for {symbol}.")
            return position
        except Exception as e:  # pragma: no cover
            log.error(
                f"Failed to retrieve {day} end of day position for {symbol} in account {self.name}: {type(e).__name__} : {e}"
            )
            raise e


class CashLedger(BaseModel):
    id = IntegerField(primary_key=True)
    external_id = TextField(unique=True)
    account = ForeignKeyField(Account, backref="deposits_and_withdraws", on_delete="CASCADE")
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
    account = ForeignKeyField(Account, backref="transactions", on_delete="CASCADE")
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
    account = ForeignKeyField(Account, backref="positions", on_delete="CASCADE")
    stock = ForeignKeyField(Stock, on_delete="CASCADE")
    size = IntegerField()
    average_price = FloatField()
    market_price = FloatField()

    class Meta:
        table_name = "position"
        indexes = ((("account", "stock", "timestamp"), True),)  # Unique constraint on account, timestamp, and stock


class Balance(BaseModel):
    id = IntegerField(primary_key=True)
    timestamp = BigIntegerField(null=False)  # Unix epoch time
    account = ForeignKeyField(Account, backref="balances", on_delete="CASCADE")
    cash = FloatField(default=0.0)

    class Meta:
        table_name = "balance"
        indexes = ((("account", "timestamp"), True),)  # Unique constraint on account and timestamp


"""
[ ] prices from exchange
[ ] transactions (deposit, withdraw, buy, sell, ...) from files
"""
