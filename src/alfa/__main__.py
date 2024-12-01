import random

from alfa.db import BaseModel, Portfolio, Stock, open_db
from alfa.util import get_current_utc_timestamp

if __name__ == "__main__":

    def display_stocks(stocks):
        for stock in stocks:
            prices = stock.prices
            for idx, price in enumerate(prices):
                print(
                    f"Price {idx}: Date {price.timestamp}, Stock {price.symbol}, Price: {price.adjusted_close}"
                )
            _ = stock.get_most_recent_price()

    def get_external_id():
        return random.random() * 1000

    db = open_db()
    db.connect()
    db.create_tables(BaseModel.get_models())

    # Add a new stock (if needed) and some prices
    p = Portfolio.get_or_none(Portfolio.name == "Theta")
    if not p:
        p = Portfolio.add_portfolio("Theta")

    if not p:
        exit()

    portfolios = Portfolio.get_portfolios()
    p = portfolios[0]

    p.start_watching("AAPL", "Apple Inc.")
    p.start_watching("TSLA")

    print(f"{p.name} watches {len(p.get_watchlist())} stocks.")

    stock = Stock.get(Stock.symbol == "AAPL")
    stock.add_price(
        timestamp=get_current_utc_timestamp(),
        open=152.0,
        high=157.0,
        low=150.0,
        close=156.0,
        adjusted_close=155.5,
        volume=1100000,
    )

    print(f"{stock.symbol} has {len(stock.prices)} prices")
    display_stocks(p.get_watchlist())

    p.deposit(get_external_id(), 100, get_current_utc_timestamp())
    p.withdraw(get_external_id(), 90, get_current_utc_timestamp())

    print(f"{p.name} cash balance is {p.cash}")
    print(f"{p.name} has {len(p.cash_ledger)} cash ledger entries.")
    print(f"{p.name} has {len(p.transaction_ledger)} transaction ledger entries.")

    for c in p.cash_ledger:
        print(
            f"{c.portfolio.name} - Cash Ledger Entry - external_id: {c.external_id}, amount: {c.amount}, type: {c.type}"
        )

    for t in p.transaction_ledger:
        print(
            f"{t.portfolio.name} - Transaction Ledger Entry - external_id: {t.external_id}, stock: {t.stock.symbol}, \
                quantity: {t.quantity}, price: {t.price}, type: {t.type}"
        )

    p.stop_watching("AAPL")
    watchlist = p.get_watchlist()
    for s in watchlist:
        print(f"{p.name} watching {s.symbol}")

    print(f"{p.name} cash balance is {p.cash}")
    print(f"{p.name} has {len(p.cash_ledger)} cash ledger entries.")
    print(f"{p.name} has {len(p.transaction_ledger)} transaction ledger entries.")

    db.close()
