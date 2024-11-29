from datetime import datetime

from alfa.db import Price, Stock


def test_add_stock(setup_database):
    stock = Stock.add_stock(symbol="AAPL", name="Apple Inc.")
    assert stock is not None
    assert stock.symbol == "AAPL"
    assert stock.name == "Apple Inc."

    # Verify the stock exists in the database
    retrieved_stock = Stock.get(Stock.symbol == "AAPL")
    assert retrieved_stock.symbol == "AAPL"
    assert retrieved_stock.name == "Apple Inc."


def test_add_stock_twice(setup_database):
    stock = Stock.add_stock(symbol="AAPL", name="Apple Inc.")
    assert stock is not None
    assert stock.symbol == "AAPL"
    assert stock.name == "Apple Inc."

    # Verify the stock exists in the database
    retrieved_stock = Stock.get(Stock.symbol == "AAPL")
    assert retrieved_stock.symbol == "AAPL"
    stock = Stock.add_stock(symbol="AAPL", name="Apple Inc.")
    assert stock is None


def test_get_stocks(setup_database):
    Stock.add_stock(symbol="AAPL", name="Apple Inc.")
    Stock.add_stock(symbol="MSFT", name="Microsoft Corporation")

    stocks = Stock.get_stocks()
    assert len(stocks) == 2
    assert stocks[0].symbol == "AAPL"
    assert stocks[1].symbol == "MSFT"


def test_delete_stock(setup_database):
    Stock.add_stock(symbol="AAPL", name="Apple Inc.")
    Stock.add_stock(symbol="MSFT", name="Microsoft Corporation")

    assert Stock.delete_stock("AAPL") is True
    assert len(Stock.get_stocks()) == 1
    assert Stock.delete_stock("AAPL") is False  # Stock already deleted


def test_delete_stock_cascades_prices(setup_database):
    stock = Stock.add_stock(symbol="AAPL", name="Apple Inc.")
    Price.add_price(
        symbol=stock.symbol,
        date=datetime(2024, 11, 28),
        open=152.0,
        high=157.0,
        low=150.0,
        close=156.0,
        adjusted_close=155.5,
        volume=1100000,
    )

    assert len(Price.select()) == 1
    stock_is_deleted = Stock.delete_stock("AAPL")
    assert stock_is_deleted
    assert len(Price.select()) == 0  # Prices should be deleted with the stock


def test_invalid_stock_deletion(setup_database):
    assert Stock.delete_stock("INVALID") is False
