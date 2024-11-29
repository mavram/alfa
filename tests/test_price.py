from datetime import datetime

from alfa.db import Price, Stock


def test_add_price(setup_database):
    # Add a stock to reference
    stock = Stock.add_stock("AAPL", "Apple Inc.")

    # Add a price for the stock
    price = Price.add_price(
        symbol=stock.symbol,
        date=datetime(2024, 11, 28),
        open=150.0,
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
    stock = Stock.add_stock("AAPL", "Apple Inc.")
    Price.add_price(
        symbol=stock.symbol,
        date=datetime(2024, 11, 27),
        open=150.0,
        high=155.0,
        low=148.0,
        close=154.0,
        adjusted_close=153.5,
        volume=1000000,
    )
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

    # Get the most recent date
    most_recent_date = Price.get_latest_date_by_symbol("AAPL")

    # Assert the most recent date is correct
    assert most_recent_date == datetime(2024, 11, 28).date()


def test_get_all_stocks_with_most_recent_date(setup_database):
    # Add multiple stocks and prices
    stock1 = Stock.add_stock("AAPL", "Apple Inc.")
    stock2 = Stock.add_stock("GOOGL", "Alphabet Inc.")

    Price.add_price(
        symbol=stock1.symbol,
        date=datetime(2024, 11, 27),
        open=150.0,
        high=155.0,
        low=148.0,
        close=154.0,
        adjusted_close=153.5,
        volume=1000000,
    )
    Price.add_price(
        symbol=stock1.symbol,
        date=datetime(2024, 11, 28),
        open=152.0,
        high=157.0,
        low=150.0,
        close=156.0,
        adjusted_close=155.5,
        volume=1100000,
    )
    Price.add_price(
        symbol=stock2.symbol,
        date=datetime(2024, 11, 26),
        open=2800.0,
        high=2850.0,
        low=2750.0,
        close=2820.0,
        adjusted_close=2815.0,
        volume=900000,
    )

    # Get all stocks with their most recent dates
    most_recent_dates = Price.get_all_symbols_with_latest_date()

    # Assert the results are correct
    assert most_recent_dates == {
        "AAPL": datetime(2024, 11, 28).date(),
        "GOOGL": datetime(2024, 11, 26).date(),
    }


def test_get_prices_by_symbol(setup_database):
    # Add a stock
    stock = Stock.add_stock(symbol="AAPL", name="Apple Inc.")

    # Add prices for the stock
    Price.add_price(
        symbol=stock.symbol,
        date=datetime(2024, 11, 27),
        open=150.0,
        high=155.0,
        low=148.0,
        close=154.0,
        adjusted_close=153.5,
        volume=1000000,
    )
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

    # Retrieve prices for the symbol
    prices = Price.get_prices_by_symbol(stock.symbol)

    # Assert the correct number of prices are retrieved
    assert len(prices) == 2

    # Assert the prices are returned in descending order by date
    assert prices[0].date == datetime(2024, 11, 27).date()
    assert prices[1].date == datetime(2024, 11, 28).date()

    # Assert the details of the first price
    assert prices[0].open == 150.0
    assert prices[0].volume == 1000000

    # Assert the details of the second price
    assert prices[1].open == 152.0
    assert prices[1].volume == 1100000
