from enum import Enum

from peewee import FloatField, ForeignKeyField, IntegerField, Model, SqliteDatabase, TextField

from alfa.config import log, settings
from alfa.utils import create_directories_for_path, get_timestamp_as_utc_str

db = SqliteDatabase(None, pragmas={"foreign_keys": 1})


def open_db():
    path = settings.DB_PATH

    log.debug(f"Initializing database at '{path}'.")
    create_directories_for_path(path)
    db.init(path)
    return db


class BaseModel(Model):
    class Meta:
        database = db

    @staticmethod
    def get_models():
        return BaseModel.__subclasses__()


def _as_validated_symbol(symbol):
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("Symbol must be a non-empty string.")
    return symbol.upper()


class Stock(BaseModel):
    id = IntegerField(primary_key=True)
    symbol = TextField(unique=True)
    name = TextField(null=True)

    def get_most_recent_price(self):
        try:
            price = self.prices.order_by(Price.timestamp.desc()).first()
            if price:
                log.debug(
                    f"{self.symbol}'s most recent price is from {get_timestamp_as_utc_str(price.timestamp)}."
                )
            else:
                log.debug(f"{self.symbol} has no price records.")
            return price
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to retrieve the most recent price for {self.symbol}: {e}")
            raise e

    def add_price(self, timestamp, open, high, low, close, adjusted_close, volume):
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
            log.debug(
                f"Added price for {self.symbol} on {get_timestamp_as_utc_str(timestamp)} successfully."
            )
            return price
        except Exception as e:  # pragma: no cover
            log.error(f"Error adding price for {self.symbol}: {e}")
            raise e


class Price(BaseModel):
    id = IntegerField(primary_key=True)
    stock = ForeignKeyField(Stock, backref="prices", on_delete="CASCADE")
    symbol = TextField()
    timestamp = IntegerField()  # Unix epoch time
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
    DEPOSIT_IN_KIND = "DEPOSIT_IN_KIND"
    SELL = "SELL"
    WITHDRAW = "WITHDRAW"


class Portfolio(BaseModel):
    id = IntegerField(primary_key=True)
    name = TextField(unique=True)
    currency = TextField(choices=[c.value for c in CurrencyType])
    cash = FloatField(default=0.0)

    @staticmethod
    def add_portfolio(name, currency=CurrencyType.USD):
        try:
            portfolio, created = Portfolio.get_or_create(name=name, defaults={"currency": currency.value})
            if created:
                log.debug(f"Created portfolio '{name}' with currency '{currency.value}'.")
            return portfolio
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to add portfolio '{name}': {e}")
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

            query = (
                StockToWatch.select()
                .join(Stock)
                .where((Stock.symbol == symbol) & (StockToWatch.portfolio == self))
            )
            return query.exists()
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to check watchlist for '{symbol}' in portfolio '{self.name}': {e}")
            raise e

    def get_position(self, symbol):
        try:
            symbol = _as_validated_symbol(symbol)
            stock = Stock.get_or_none(Stock.symbol == symbol)
            if not stock:
                log.debug(f"Stock '{symbol}' does not exist in the database.")
                return None
            return Position.get_or_none((Position.portfolio == self) & (Position.stock == stock))
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to get position for '{symbol}' in portfolio '{self.name}': {e}")
            raise e

    def start_watching(self, symbol, name=None):
        try:
            symbol = _as_validated_symbol(symbol)

            stock, created = Stock.get_or_create(symbol=symbol, defaults={"name": name})
            if created:
                log.debug(f"Portfolio '{self.name}' added new stock '{symbol}'.")

            if self.is_watching(symbol):
                log.debug(f"Portfolio '{self.name}' is already watching '{symbol}'.")
                return stock

            StockToWatch.create(stock=stock, portfolio=self)
            log.debug(f"Portfolio '{self.name}' started watching '{symbol}'.")

            return stock
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to add '{symbol}' to watchlist in portfolio '{self.name}': {e}")
            raise e

    def stop_watching(self, symbol):
        try:
            symbol = _as_validated_symbol(symbol)

            if not self.is_watching(symbol):
                log.debug(f"Portfolio '{self.name}' is not watching '{symbol}'.")
                return

            if self.get_position(symbol):
                log.debug(
                    f"Cannot remove '{symbol}' from watchlist in portfolio '{self.name}' due to active position."
                )
                return

            stock = Stock.get_or_none(Stock.symbol == symbol)
            rows_deleted = (
                StockToWatch.delete()
                .where((StockToWatch.stock == stock) & (StockToWatch.portfolio == self))
                .execute()
            )
            if rows_deleted > 0:
                log.debug(f"Removed '{symbol}' from watchlist in portfolio '{self.name}'.")
            else:  # pragma: no cover
                log.debug(f"No watchlist entry found for '{symbol}' in portfolio '{self.name}'.")
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to remove '{symbol}' from watchlist in portfolio '{self.name}': {e}")
            raise e

    def get_watchlist(self):
        try:
            return list(Stock.select().join(StockToWatch).where(StockToWatch.portfolio == self))
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to retrieve watchlist for portfolio '{self.name}': {e}")
            raise e

    def deposit(self, external_id, timestamp, amount, fees=0.0):
        try:
            with db.atomic():
                total_amount_to_deposit = amount - fees
                CashLedger.create(
                    external_id=external_id,
                    portfolio=self,
                    timestamp=timestamp,
                    amount=total_amount_to_deposit,
                    type=TransactionType.DEPOSIT.value,
                    fees=fees,
                )

                self._create_or_update_cash_balance(total_amount_to_deposit)

            log.info(f"Deposited {amount} {self.currency} into portfolio '{self.name}'.")
            return self
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to deposit {amount} {self.currency} into portfolio '{self.name}': {e}")
            raise e

    def withdraw(self, external_id, timestamp, amount, fees=0.0):
        try:
            with db.atomic():
                total_amount_to_withdraw = amount + fees
                if total_amount_to_withdraw > self.cash:
                    raise ValueError(f"Withdrawal amount {amount} and fees {fees} exceeds vailable cash {self.cash} in portfolio '{self.name}'.")

                CashLedger.create(
                    external_id=external_id,
                    portfolio=self,
                    timestamp=timestamp,
                    amount=-amount,  # Negative amount indicates withdrawal
                    type=TransactionType.WITHDRAW.value,
                    fees=fees,
                )

                self._create_or_update_cash_balance(-total_amount_to_withdraw)

            log.info(f"Withdrew {amount} {self.currency} from portfolio '{self.name}'.")
            return self
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to withdraw {amount} {self.currency} from portfolio '{self.name}': {e}")
            raise e

    def _create_or_update_cash_balance(self, amount):
        self.cash += amount
        self.save()

    def _create_or_update_position(self, symbol, quantity, price):
        try:
            stock = Stock.get(Stock.symbol == symbol)
            position, created = Position.get_or_create(
                portfolio=self, stock=stock, defaults={"size": 0, "average_price": 0.0}
            )

            if created:
                log.debug(f"Created new position for '{symbol}' in portfolio '{self.name}'.")

            new_size = position.size + quantity
            if new_size < 0:
                raise ValueError(
                    f"Cannot remove {abs(quantity)} shares from '{symbol}'; only {position.size} available."
                )

            if new_size == 0:
                log.debug(f"Liquidating position for '{symbol}' in portfolio '{self.name}'.")
                position.delete_instance()
                return None

            if quantity > 0:
                total_cost = (position.average_price * position.size) + (price * quantity)
                position.average_price = total_cost / new_size

            position.size = new_size
            position.save()

            log.debug(
                f"Updated position for '{symbol}' in portfolio '{self.name}': "
                f"Size={position.size}, Average Price={position.average_price:.2f}"
            )

            return position
        except Exception as e:
            log.error(
                f"Failed to create or update position for '{symbol}' in portfolio '{self.name}': {e}"
            )
            raise e

    def buy(self, external_id, timestamp, symbol, quantity, price, fees=0.0):
        try:
            symbol = _as_validated_symbol(symbol)

            with db.atomic():
                total_cost = quantity * price + fees
                if self.cash < total_cost:
                    log.error(
                        f"Insufficient cash to buy {quantity} shares of '{symbol}'. "
                        f"Required: {total_cost}, Available: {self.cash}."
                    )
                    raise ValueError(
                        f"Portfolio '{self.name}' does not have sufficient cash to buy {quantity} shares of '{symbol}'."
                    )

                # Update cash balance
                self._create_or_update_cash_balance(-total_cost)

                # Add symbol to watchlist
                self.start_watching(symbol)

                # Update position
                self._create_or_update_position(symbol, quantity, price)

                # Record the transaction
                stock = Stock.get(Stock.symbol == symbol)
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
                f"Bought {quantity} shares of '{symbol}' at ${price:.2f} each. "
                f"Total Cost: ${total_cost:.2f}. Fees: ${fees:.2f}."
            )
            return self
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to buy {quantity} shares of '{symbol}' at ${price:.2f}: {e}")
            raise e

    def deposit_in_kind(self, external_id, timestamp, symbol, quantity, cost_basis_per_share, fees=0.0):
        try:
            symbol = _as_validated_symbol(symbol)

            with db.atomic():
                total_fees = fees
                if self.cash < total_fees:
                    log.error(
                        f"Insufficient cash to cover fees for depositing {quantity} shares of '{symbol}'. "
                        f"Required Fees: ${total_fees:.2f}, Available Cash: ${self.cash:.2f}."
                    )
                    raise ValueError(
                        f"Portfolio '{self.name}' does not have sufficient cash to cover fees "
                        f"for depositing {quantity} shares of '{symbol}'."
                    )

                # Update cash balance to cover fees
                self._create_or_update_cash_balance(-total_fees)

                # Add symbol to watchlist
                self.start_watching(symbol)

                # Update position
                self._create_or_update_position(symbol, quantity, cost_basis_per_share)

                # Record the transaction
                stock = Stock.get(Stock.symbol == symbol)
                TransactionLedger.create(
                    external_id=external_id,
                    portfolio=self,
                    timestamp=timestamp,
                    stock=stock,
                    quantity=quantity,
                    price=cost_basis_per_share,
                    type=TransactionType.DEPOSIT_IN_KIND.value,
                    fees=fees,
                )

            log.info(
                f"Deposited {quantity} shares of '{symbol}' at ${cost_basis_per_share:.2f} each. "
                f"Fees: ${fees:.2f}."
            )
            return self
        except Exception as e:  # pragma: no cover
            log.error(
                f"Failed to deposit {quantity} shares of '{symbol}' at ${cost_basis_per_share:.2f}: {e}"
            )
            raise e

    def sell(self, external_id, timestamp, symbol, quantity, price, fees=0.0):
        try:
            symbol = _as_validated_symbol(symbol)

            with db.atomic():
                position = self.get_position(symbol)
                if not position:
                    log.error(f"Portfolio '{self.name}' has no position in '{symbol}'.")
                    raise ValueError(f"No active position in '{symbol}' to sell.")

                if quantity > position.size:
                    raise ValueError(f"Requested to sell {quantity} shares of '{symbol}' exceeds current position of {position.size} shares.")

                total_proceeds = quantity * price - fees

                # Update cash balance
                self._create_or_update_cash_balance(total_proceeds)

                # Update position
                position = self._create_or_update_position(symbol, -quantity, price)
                if not position:
                    # Position was liquidated, stop watching
                    self.stop_watching(symbol)

                # Record the transaction
                stock = Stock.get(Stock.symbol == symbol)
                TransactionLedger.create(
                    external_id=external_id,
                    portfolio=self,
                    timestamp=timestamp,
                    stock=stock,
                    quantity=-quantity,  # Negative quantity indicates sale
                    price=price,
                    type=TransactionType.SELL.value,
                    fees=fees,
                )

            log.info(
                f"Sold {quantity} shares of '{symbol}' at ${price:.2f} each. "
                f"Total Proceeds: ${total_proceeds:.2f}. Fees: ${fees:.2f}."
            )
            return self
        except Exception as e:  # pragma: no cover
            log.error(f"Failed to sell {quantity} shares of '{symbol}' at ${price:.2f}: {e}")
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
    timestamp = IntegerField()  # Unix epoch time
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
    timestamp = IntegerField(null=False)  # Unix epoch time
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
    portfolio = ForeignKeyField(Portfolio, backref="positions", on_delete="CASCADE")
    stock = ForeignKeyField(Stock, on_delete="CASCADE")
    size = IntegerField()
    average_price = FloatField()

    class Meta:
        table_name = "position"
        indexes = ((("portfolio", "stock"), True),)  # Unique constraint on portfolio and stock


"""
TODO:
[] end-of-day balance
[] end-of-day positions
[] repo of deposits and withdraws
[] repo of transactions
[] batch processor

"""
