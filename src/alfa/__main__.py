from datetime import datetime

from alfa.db import Price, Stock, open_db
from alfa.portfolio import Portfolio


def display_stocks(stocks):
    for stock in stocks:
        prices = stock.prices
        for idx, price in enumerate(prices):
            print(
                f"Price{idx}: Date {price.timestamp}, Stock {price.symbol}, Price: {price.adjusted_close}"
            )
        print(f"Most recent price is {stock.get_most_recent_price().timestamp}")


if __name__ == "__main__":
    p = Portfolio()
    p.deposit(16000)
    p.buy("TSLA", 100, 150)
    p.buy("TSLA", 100, 170)
    p.sell("TSLA", 50, 180)
    p.buy("TSLA", 300, 180)
    p.sell("NVDA", 300, 180)
    p.sell("TSLA", 1000, 200)
    p.deposit_stock("TSLA", 1000, 120)
    p.withdraw(100000)

    db = open_db()
    db.connect()
    db.create_tables([Stock, Price])

    # Add a new stock (if needed) and some prices
    stock = Stock.get_or_none(Stock.symbol == "AAPL")
    if not stock:
        stock = Stock.add_stock("AAPL", "Apple Inc.")

    if not stock:
        exit()

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
    display_stocks(Stock.get_stocks())
    stock_is_deleted = Stock.delete_stock("AAPL")
    assert stock_is_deleted
    display_stocks(Stock.get_stocks())

    db.close()
