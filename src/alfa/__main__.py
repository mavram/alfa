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
    Stock.add_stock("AAPL", "Apple Inc.")
    Stock.add_stock("MSFT", "Microsoft Corporation")

    # Retrieve all stocks
    stocks = Stock.get_stocks()
    for stock in stocks:
        print(f"Stock Id: {stock.id}, Symbol: {stock.symbol}, Name: {stock.name}")

    db.close()
