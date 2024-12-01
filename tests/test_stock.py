from datetime import datetime

from alfa.db import Stock


def test_add_stock(setup_database):
    stock = Stock.add_stock("AAPL", "Apple Inc.")
    assert stock is not None
    assert stock.symbol == "AAPL"
    assert stock.name == "Apple Inc."

    # Attempt to add duplicate stock
    duplicate_stock = Stock.add_stock("AAPL", "Apple Inc.")
    assert duplicate_stock is None  # Should fail due to unique constraint


def test_add_price(setup_database):
    stock = Stock.add_stock("AAPL", "Apple Inc.")
    assert stock is not None

    # Add a price for the stock
    price = stock.add_price(
        timestamp=datetime(2023, 11, 30, 10, 0),
        open=150.0,
        high=155.0,
        low=148.0,
        close=154.0,
        adjusted_close=154.0,
        volume=1000000,
    )
    assert price is not None
    assert price.open == 150.0
    assert price.close == 154.0

    # Retrieve the most recent price
    most_recent_price = stock.get_most_recent_price()
    assert most_recent_price is not None
    assert most_recent_price.timestamp == datetime(2023, 11, 30, 10, 0)


def test_get_most_recent_price_no_prices(setup_database):
    # Create a stock
    stock = Stock.add_stock("AAPL", "Apple Inc.")
    assert stock is not None

    # Call get_most_recent_price when there are no prices
    most_recent_price = stock.get_most_recent_price()

    # Assert that the result is None
    assert most_recent_price is None
