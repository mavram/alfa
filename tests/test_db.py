from datetime import datetime

import pytest

from alfa.db import Stock


def test_add_stock(setup_database):
    stock = Stock.add_stock(symbol="AAPL", name="Apple Inc.")
    assert stock is not None
    assert stock.symbol == "AAPL"
    assert stock.name == "Apple Inc."
    retrieved_stock = Stock.get(Stock.symbol == "AAPL")
    assert retrieved_stock.name == "Apple Inc."


def test_get_stocks(setup_database):
    Stock.add_stock(symbol="AAPL", name="Apple Inc.")
    Stock.add_stock(symbol="MSFT", name="Microsoft Corp.")
    stocks = Stock.get_stocks()
    assert len(stocks) == 2
    assert stocks[0].symbol == "AAPL"
    assert stocks[1].symbol == "MSFT"


def test_delete_stock(setup_database):
    Stock.add_stock(symbol="AAPL", name="Apple Inc.")
    assert Stock.delete_stock("AAPL") is True
    with pytest.raises(Stock.DoesNotExist):
        Stock.get(Stock.symbol == "AAPL")


def test_add_price(setup_database):
    stock = Stock.add_stock(symbol="AAPL", name="Apple Inc.")
    timestamp = datetime(2024, 11, 29, 12, 0, 0)
    price = stock.add_price(
        timestamp=timestamp,
        open=200.0,
        high=210.0,
        low=195.0,
        close=205.0,
        adjusted_close=204.5,
        volume=1000000,
    )
    assert price is not None
    assert price.symbol == "AAPL"
    assert price.timestamp == timestamp
    assert price.close == 205.0
    assert len(stock.prices) == 1


def test_get_most_recent_price(setup_database):
    stock = Stock.add_stock(symbol="AAPL", name="Apple Inc.")
    timestamp1 = datetime(2024, 11, 28, 12, 0, 0)
    timestamp2 = datetime(2024, 11, 29, 12, 0, 0)
    stock.add_price(
        timestamp=timestamp1,
        open=190.0,
        high=200.0,
        low=185.0,
        close=195.0,
        adjusted_close=194.5,
        volume=800000,
    )
    stock.add_price(
        timestamp=timestamp2,
        open=200.0,
        high=210.0,
        low=195.0,
        close=205.0,
        adjusted_close=204.5,
        volume=1000000,
    )
    recent_price = stock.get_most_recent_price()
    assert recent_price.timestamp == timestamp2


def test_delete_nonexistent_stock(setup_database):
    result = Stock.delete_stock("NONEXISTENT")
    assert result is False
