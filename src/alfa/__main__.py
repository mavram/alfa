from datetime import datetime

from alfa.db import BaseModel, Portfolio, Stock, open_db

if __name__ == "__main__":

    def display_stocks(stocks):
        for stock in stocks:
            prices = stock.prices
            for idx, price in enumerate(prices):
                print(
                    f"Price {idx}: Date {price.timestamp}, Stock {price.symbol}, Price: {price.adjusted_close}"
                )

            most_recent_price = stock.get_most_recent_price()
            if most_recent_price:
                print(f"Most recent price is {most_recent_price.timestamp}")

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
    for p in portfolios:
        print(f"{p.name} uses {p.get_currency()}")

    p = portfolios[0]

    p.start_watching("AAPL", "Apple Inc.")
    p.start_watching("TSLA")

    print(f"{p.name} watches {len(p.watchlist)} stocks.")

    stock = Stock.get(Stock.symbol == "AAPL")
    stock.add_price(
        timestamp=datetime.now(),
        open=152.0,
        high=157.0,
        low=150.0,
        close=156.0,
        adjusted_close=155.5,
        volume=1100000,
    )

    print(f"{stock.symbol} has {len(stock.prices)} prices")
    # display_stocks(p.watchlist)

    db.close()
