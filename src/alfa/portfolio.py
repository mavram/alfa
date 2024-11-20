from dynaconf import settings

from alfa.log import log


class Portfolio:
    """
    A class representing a portfolio of financial assets, including cash, stock positions,
    and a watchlist of stocks to monitor.

    Attributes:
        name (str): The name of the portfolio. Defaults to settings.PORTFOLIO_NAME if not provided.
        cash (float): The amount of cash available in the portfolio.
        positions (dict): A dictionary of stock positions, with stock symbols as keys and dictionaries
                          containing size and average price as values.
        stocks_to_watch (set): A set of stock symbols the user is monitoring.
    """

    def __init__(self, name=None):
        """
        Initializes a Portfolio instance.

        Args:
            name (str, optional): The name of the portfolio. Defaults to None, in which case
                                  settings.PORTFOLIO_NAME is used.
        """
        self.name = name or settings.PORTFOLIO_NAME
        # TODO: load from db
        self.cash = 0
        self.positions = {}
        self.stocks_to_watch = set()

    def get_positions(self):
        """
        Retrieves a list of all stock symbols currently in the portfolio.

        Returns:
            list: A list of stock symbols.
        """
        return list(self.positions.keys())

    def get_stocks_to_watch(self):
        """
        Retrieves a list of stock symbols being monitored.

        Returns:
            list: A list of stock symbols being watched.
        """
        return list(self.stocks_to_watch)

    def get_position_size(self, symbol):
        """
        Retrieves the size of the position for a given stock symbol.

        Args:
            symbol (str): The stock symbol.

        Returns:
            int: The size of the position, or 0 if the stock is not held.
        """
        symbol = symbol.upper()
        return 0 if symbol not in self.positions else self.positions[symbol]["size"]

    def get_cash(self):
        """
        Retrieves the current cash balance of the portfolio.

        Returns:
            float: The current cash balance.
        """
        return self.cash

    def sell(self, symbol, qty, price):
        """
        Sells a specified quantity of a stock at a given price. The quantity will not exceed position size.

        Args:
            symbol (str): The stock symbol.
            qty (int): The quantity to sell.
            price (float): The price per share.

        Returns:
            bool: False if the stock position does not exist, True otherwise.
        """
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
        """
        Buys a specified quantity of a stock at a given price.

        Args:
            symbol (str): The stock symbol.
            qty (int): The quantity to buy.
            price (float): The price per share.

        Returns:
            bool: False if there is insufficient cash, True otherwise.
        """
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

    def withdraw(self, amount):
        """
        Withdraws cash from the portfolio. The amount withdrawn will note exceeds existing cash balance.

        Args:
            amount (float): The amount to withdraw.
        """
        if amount > self.cash:
            log.info(f"Requested amount {amount} is capped at {self.cash} by {self.name}'s cash balance.")
            amount = self.cash
        self.cash -= amount
        log.info(f"WITHDRAW {amount}")

    def deposit(self, amount):
        """
        Deposits cash into the portfolio.

        Args:
            amount (float): The amount to deposit.
        """
        self.cash += amount
        log.info(f"DEPOSIT {amount}")

    def deposit_stock(self, symbol, qty, cost_basis_per_share, gain_loss=None):
        """
        Deposits a stock position into the portfolio.

        Args:
            symbol (str): The stock symbol.
            qty (int): The quantity of stock.
            cost_basis_per_share (float): The cost basis per share.
            gain_loss (str, optional): Additional gain/loss information.
        """
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

    def start_watching(self, symbol):
        """
        Adds a stock symbol to the watchlist.

        Args:
            symbol (str): The stock symbol.
        """
        self.stocks_to_watch.add(symbol)

    def stop_watching(self, symbol):
        """
        Removes a stock symbol from the watchlist.

        Args:
            symbol (str): The stock symbol.
        """
        self.stocks_to_watch.discard(symbol)

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
        # j) Generate eod positions ???

        pass
