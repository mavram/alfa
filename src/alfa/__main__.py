from datetime import datetime

from alfa.db import Price, Stock, open_db
from alfa.portfolio import Portfolio

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

    # Add a new stock (if needed)
    symbols = Stock.get_symbols()
    if "AAPL" not in symbols:
        stock = Stock.add_stock("AAPL", "Apple Inc.")
    Price.add_price(
        symbol="AAPL",
        timestamp=datetime.now(),
        open=152.0,
        high=157.0,
        low=150.0,
        close=156.0,
        adjusted_close=155.5,
        volume=1100000,
    )

    stocks = Stock.get_stocks()
    print(f"Found {len(stocks)} stocks")
    for stock in stocks:
        prices = stock.prices
        print(f"Found {len(prices)} prices")
        for price in prices:
            print(f"Date {price.timestamp}, Stock {price.symbol}, Price: {price.adjusted_close}")
        print(f"Most recent price is {stock.get_most_recent_price()}")

    stock_is_deleted = Stock.delete_stock("AAPL")
    assert stock_is_deleted

    stocks = Stock.get_stocks()
    print(f"Found {len(stocks)} stocks")
    for stock in stocks:
        prices = stock.prices
        print(f"Found {len(prices)} prices")
        for price in prices:
            print(f"Date {price.timestamp}, Stock {price.symbol}, Price: {price.adjusted_close}")

    db.close()
