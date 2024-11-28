from datetime import datetime

from alfa.db import Price, Stock


def test_add_price(setup_database):
    # Add a stock to reference
    stock = Stock.create(symbol="AAPL", name="Apple Inc.")

    # Add a price for the stock
    price = Price.add_price(
        symbol=stock.symbol,
        date=datetime(2024, 11, 28),
        open_price=150.0,
        high=155.0,
        low=148.0,
        close=154.0,
        adjusted_close=153.5,
        volume=1000000,
    )

    # Assert the price was added correctly
    assert price is not None
    assert price.symbol == "AAPL"
    assert price.date == datetime(2024, 11, 28)
    assert price.open == 150.0
    assert price.high == 155.0
    assert price.low == 148.0
    assert price.close == 154.0
    assert price.adjusted_close == 153.5
    assert price.volume == 1000000


def test_get_latest_price_by_stock(setup_database):
    # Add a stock and multiple prices
    stock = Stock.create(symbol="AAPL", name="Apple Inc.")
    Price.add_price(
        symbol=stock.symbol,
        date=datetime(2024, 11, 27),
        open_price=150.0,
        high=155.0,
        low=148.0,
        close=154.0,
        adjusted_close=153.5,
        volume=1000000,
    )
    Price.add_price(
        symbol=stock.symbol,
        date=datetime(2024, 11, 28),
        open_price=152.0,
        high=157.0,
        low=150.0,
        close=156.0,
        adjusted_close=155.5,
        volume=1100000,
    )

    # Get the most recent date
    most_recent_date = Price.get_latest_price_by_symbol("AAPL")

    # Assert the most recent date is correct
    assert most_recent_date == datetime(2024, 11, 28).date()


def test_get_all_stocks_with_most_recent_date(setup_database):
    # Add multiple stocks and prices
    stock1 = Stock.create(symbol="AAPL", name="Apple Inc.")
    stock2 = Stock.create(symbol="GOOGL", name="Alphabet Inc.")

    Price.add_price(
        symbol=stock1.symbol,
        date=datetime(2024, 11, 27),
        open_price=150.0,
        high=155.0,
        low=148.0,
        close=154.0,
        adjusted_close=153.5,
        volume=1000000,
    )
    Price.add_price(
        symbol=stock1.symbol,
        date=datetime(2024, 11, 28),
        open_price=152.0,
        high=157.0,
        low=150.0,
        close=156.0,
        adjusted_close=155.5,
        volume=1100000,
    )
    Price.add_price(
        symbol=stock2.symbol,
        date=datetime(2024, 11, 26),
        open_price=2800.0,
        high=2850.0,
        low=2750.0,
        close=2820.0,
        adjusted_close=2815.0,
        volume=900000,
    )

    # Get all stocks with their most recent dates
    most_recent_dates = Price.get_all_symbols_with_most_recent_date()

    # Assert the results are correct
    assert most_recent_dates == {
        "AAPL": datetime(2024, 11, 28).date(),
        "GOOGL": datetime(2024, 11, 26).date(),
    }
