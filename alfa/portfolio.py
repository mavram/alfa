from dynaconf import settings

from alfa.logging import log


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
        return 0 if symbol not in self.positions else self.positions[symbol]["size"]

    def get_cash(self):
        return self.cash

    def sell(self, symbol, qty, price):
        symbol = symbol.upper()
        if self.get_position_size(symbol) == 0:
            log.error(f"Portfolio {self.name} has no position in {symbol}.")
            return False

        size = self.positions[symbol]["size"]

        if qty > size:
            # Limit to position size
            log.info(
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

        # Update cash balance
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
            # Initialize position
            self.positions[symbol] = {"size": 0, "average_price": 0.0}

        size = self.positions[symbol]["size"]
        average_price = self.positions[symbol]["average_price"]

        # New position size
        new_size = size + qty

        # Update position with weighted average price
        self.positions[symbol]["average_price"] = (average_price * size + price * qty) / new_size
        # Update position size
        self.positions[symbol]["size"] = new_size

        # Update cash balance
        self.cash -= qty * price

        log.info(f"BUY {qty} {symbol} @ {price}")

    def withdraw(self, amount):
        pass

    def withdraw_stock(self, symbol, qty):
        symbol = symbol.upper()
        pass

    def deposit(self, amount):
        self.cash += amount
        log.info(f"DEPOSIT {amount}")

    def deposit_stock(self, symbol, qty):
        symbol = symbol.upper()
        pass
