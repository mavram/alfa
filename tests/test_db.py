import os
from datetime import date

import pytest
from dynaconf import settings

from alfa.db import Price, Stock, open_db


@pytest.fixture(scope="function")
def setup_database():
    """
    Fixture to initialize and clean up the database for each test.
    """
    db = open_db()
    db.connect()
    db.create_tables([Stock, Price])
    yield db  # Provides the initialized database to the test
    db.drop_tables([Stock, Price])
    db.close()
    # Remove test database
    os.remove(settings.DB_PATH)


def test_add_stock(setup_database):
    """Test adding a stock to the database."""
    stock = Stock.add_stock(symbol="AAPL", name="Apple Inc.")
    assert stock is not None
    assert stock.symbol == "AAPL"
    assert stock.name == "Apple Inc."

    # Verify the stock exists in the database
    retrieved_stock = Stock.get(Stock.symbol == "AAPL")
    assert retrieved_stock.symbol == "AAPL"
    assert retrieved_stock.name == "Apple Inc."


def test_add_stock_twice(setup_database):
    """Test adding a stock to the database twice."""
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
    """Test retrieving all stocks from the database."""
    Stock.add_stock(symbol="AAPL", name="Apple Inc.")
    Stock.add_stock(symbol="MSFT", name="Microsoft Corporation")

    stocks = Stock.get_stocks()
    assert len(stocks) == 2
    assert stocks[0].symbol == "AAPL"
    assert stocks[1].symbol == "MSFT"


def test_delete_stock(setup_database):
    """Test deleting a stock by its symbol."""
    Stock.add_stock(symbol="AAPL", name="Apple Inc.")
    Stock.add_stock(symbol="MSFT", name="Microsoft Corporation")

    assert Stock.delete_stock("AAPL") is True
    assert len(Stock.get_stocks()) == 1
    assert Stock.delete_stock("AAPL") is False  # Stock already deleted


def test_add_price(setup_database):
    """Test adding a price entry for a stock."""
    stock = Stock.add_stock(symbol="AAPL", name="Apple Inc.")
    price = Price.create(
        stock_id=stock.id,
        date=date(2024, 1, 1),
        open=100.0,
        high=110.0,
        low=95.0,
        close=105.0,
        adjusted_close=105.0,
        volume=1000000,
    )
    assert price is not None
    assert price.stock_id.id == stock.id
    assert price.date == date(2024, 1, 1)
    assert price.open == 100.0


# def test_delete_stock_cascades_prices(setup_database):
#     """Test that deleting a stock cascades to delete associated prices."""
#     stock = Stock.add_stock(symbol="AAPL", name="Apple Inc.")
#     Price.create(
#         stock_id=stock.id,
#         date=date(2024, 1, 1),
#         open=100.0,
#         high=110.0,
#         low=95.0,
#         close=105.0,
#         adjusted_close=105.0,
#         volume=1000000,
#     )

#     assert len(Price.select()) == 1
#     Stock.delete_stock("AAPL")
#     assert len(Price.select()) == 0  # Prices should be deleted with the stock


def test_invalid_stock_deletion(setup_database):
    """Test attempting to delete a stock that doesn't exist."""
    assert Stock.delete_stock("INVALID") is False
