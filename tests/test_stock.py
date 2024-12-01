from datetime import datetime, timezone

from alfa.db import Stock


def test_add_stock_success(setup_database):
    symbol = "AAPL"
    name = "Apple Inc."
    stock = Stock.add_stock(symbol=symbol, name=name)
    assert stock is not None
    assert stock.symbol == symbol
    assert stock.name == name

    # Verify that the stock is in the database
    stock_from_db = Stock.get(Stock.symbol == symbol)
    assert stock_from_db.symbol == symbol
    assert stock_from_db.name == name


def test_add_stock_duplicate_symbol(setup_database):
    symbol = "AAPL"
    name1 = "Apple Inc."
    name2 = "Apple Corporation"

    # Add the stock the first time
    stock1 = Stock.add_stock(symbol=symbol, name=name1)
    assert stock1 is not None

    # Try to add the same stock again
    stock2 = Stock.add_stock(symbol=symbol, name=name2)
    assert stock2 is None  # Should return None due to duplicate symbol


def test_get_most_recent_price_no_prices(setup_database):
    symbol = "AAPL"
    name = "Apple Inc."
    stock = Stock.add_stock(symbol=symbol, name=name)
    assert stock is not None

    recent_price = stock.get_most_recent_price()
    assert recent_price is None


def test_get_most_recent_price_with_prices(setup_database):
    symbol = "AAPL"
    name = "Apple Inc."
    stock = Stock.add_stock(symbol=symbol, name=name)
    assert stock is not None

    # Add multiple prices
    timestamp1 = int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp())
    timestamp2 = int(datetime(2023, 1, 2, tzinfo=timezone.utc).timestamp())
    price1 = stock.add_price(
        timestamp=timestamp1,
        open=150.0,
        high=155.0,
        low=149.0,
        close=154.0,
        adjusted_close=154.0,
        volume=1000000,
    )
    assert price1 is not None

    price2 = stock.add_price(
        timestamp=timestamp2,
        open=155.0,
        high=160.0,
        low=154.0,
        close=158.0,
        adjusted_close=158.0,
        volume=1200000,
    )
    assert price2 is not None

    recent_price = stock.get_most_recent_price()
    assert recent_price is not None
    assert recent_price.timestamp == timestamp2
    assert recent_price.close == 158.0


def test_add_price_success(setup_database):
    symbol = "AAPL"
    name = "Apple Inc."
    stock = Stock.add_stock(symbol=symbol, name=name)
    assert stock is not None

    timestamp = int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp())
    price = stock.add_price(
        timestamp=timestamp,
        open=150.0,
        high=155.0,
        low=149.0,
        close=154.0,
        adjusted_close=154.0,
        volume=1000000,
    )
    assert price is not None
    assert price.stock_id == stock.id
    assert price.symbol == symbol
    assert price.timestamp == timestamp
    assert price.open == 150.0
    assert price.high == 155.0
    assert price.low == 149.0
    assert price.close == 154.0
    assert price.adjusted_close == 154.0
    assert price.volume == 1000000


def test_add_price_invalid_data(setup_database):
    symbol = "AAPL"
    name = "Apple Inc."
    stock = Stock.add_stock(symbol=symbol, name=name)
    assert stock is not None

    # Try to add a price with missing required fields
    timestamp = int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp())
    price = stock.add_price(
        timestamp=timestamp,
        open=None,  # Invalid data: open price is None
        high=155.0,
        low=149.0,
        close=154.0,
        adjusted_close=154.0,
        volume=1000000,
    )
    assert price is None  # Should return None due to error


def test_add_price_to_nonexistent_stock(setup_database):
    # Create a stock and delete it
    symbol = "AAPL"
    name = "Apple Inc."
    stock = Stock.add_stock(symbol=symbol, name=name)
    assert stock is not None

    # Delete the stock
    stock.delete_instance()

    # Try to add a price to the deleted stock
    timestamp = int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp())
    price = stock.add_price(
        timestamp=timestamp,
        open=150.0,
        high=155.0,
        low=149.0,
        close=154.0,
        adjusted_close=154.0,
        volume=1000000,
    )
    assert price is None  # Should return None due to error


def test_get_most_recent_price_after_deleting_prices(setup_database):
    symbol = "AAPL"
    name = "Apple Inc."
    stock = Stock.add_stock(symbol=symbol, name=name)
    assert stock is not None

    # Add multiple prices
    timestamp1 = int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp())
    timestamp2 = int(datetime(2023, 1, 2, tzinfo=timezone.utc).timestamp())
    timestamp3 = int(datetime(2023, 1, 3, tzinfo=timezone.utc).timestamp())

    price1 = stock.add_price(
        timestamp=timestamp1,
        open=150.0,
        high=152.0,
        low=148.0,
        close=151.0,
        adjusted_close=151.0,
        volume=1000000,
    )
    assert price1 is not None

    price2 = stock.add_price(
        timestamp=timestamp2,
        open=152.0,
        high=156.0,
        low=151.0,
        close=155.0,
        adjusted_close=155.0,
        volume=1100000,
    )
    assert price2 is not None

    price3 = stock.add_price(
        timestamp=timestamp3,
        open=155.0,
        high=157.0,
        low=154.0,
        close=156.0,
        adjusted_close=156.0,
        volume=1200000,
    )
    assert price3 is not None

    # Delete the most recent price
    price3.delete_instance()

    recent_price = stock.get_most_recent_price()
    assert recent_price is not None
    assert recent_price.timestamp == timestamp2
    assert recent_price.close == 155.0


def test_add_stock_without_name(setup_database):
    symbol = "AAPL"
    stock = Stock.add_stock(symbol=symbol)
    assert stock is not None
    assert stock.symbol == symbol
    assert stock.name is None


def test_add_stock_with_empty_symbol(setup_database):
    symbol = ""
    name = "Some Company"
    stock = Stock.add_stock(symbol=symbol, name=name)
    assert stock is None  # Should return None due to invalid symbol


def test_add_stock_with_null_symbol(setup_database):
    symbol = None
    name = "Some Company"
    stock = Stock.add_stock(symbol=symbol, name=name)
    assert stock is None  # Should return None due to invalid symbol


def test_add_price_with_negative_volume(setup_database):
    symbol = "AAPL"
    name = "Apple Inc."
    stock = Stock.add_stock(symbol=symbol, name=name)
    assert stock is not None

    timestamp = int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp())
    price = stock.add_price(
        timestamp=timestamp,
        open=150.0,
        high=155.0,
        low=149.0,
        close=154.0,
        adjusted_close=154.0,
        volume=-1000000,  # Invalid volume
    )
    assert price is None  # Should return None due to error
