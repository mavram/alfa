from alfa.db import Currency, Portfolio, Stock


def test_add_portfolio(setup_database):
    portfolio = Portfolio.add_portfolio("__theta__", Currency.USD)
    assert portfolio is not None
    assert portfolio.name == "__theta__"
    assert portfolio.currency == "USD"

    # Attempt to add duplicate portfolio
    duplicate_portfolio = Portfolio.add_portfolio("__theta__", Currency.USD)
    assert duplicate_portfolio is None  # Should fail due to unique constraint


def test_start_watching(setup_database):
    # Create portfolio and stock
    portfolio = Portfolio.add_portfolio("__theta__", Currency.USD)
    assert portfolio is not None

    stock = Stock.add_stock("AAPL", "Apple Inc.")
    assert stock is not None

    # Add stock to watchlist
    added = portfolio.start_watching("AAPL", "Apple Inc.")
    assert added is True

    # Verify watchlist contains the stock
    watchlist = portfolio.get_watchlist()
    assert len(watchlist) == 1
    assert watchlist[0].symbol == "AAPL"

    # Attempt to add the same stock again
    added_again = portfolio.start_watching("AAPL")
    assert added_again is True  # Method does nothing if already watched
    assert len(portfolio.get_watchlist()) == 1  # No duplicate entries


def test_stop_watching(setup_database):
    # Create portfolio and stock
    portfolio = Portfolio.add_portfolio("__theta__", Currency.USD)
    stock = Stock.add_stock("AAPL", "Apple Inc.")
    portfolio.start_watching(stock.symbol, "Apple Inc.")

    # Remove stock from watchlist
    removed = portfolio.stop_watching("AAPL")
    assert removed is True

    # Verify watchlist is empty
    watchlist = portfolio.get_watchlist()
    assert len(watchlist) == 0

    # Attempt to remove non-existent stock
    removed_again = portfolio.stop_watching("AAPL")
    assert removed_again is False


def test_get_currency(setup_database):
    portfolio = Portfolio.add_portfolio("__theta__", Currency.CAD)
    assert portfolio.get_currency() == Currency.CAD

    portfolio_usd = Portfolio.add_portfolio("Growth Portfolio", Currency.USD)
    assert portfolio_usd.get_currency() == Currency.USD


def test_get_portfolios(setup_database):
    # Add portfolios
    Portfolio.add_portfolio("Tech Portfolio", Currency.USD)
    Portfolio.add_portfolio("Growth Portfolio", Currency.CAD)
    Portfolio.add_portfolio("Dividend Portfolio", Currency.USD)

    # Retrieve portfolios
    portfolios = Portfolio.get_portfolios()

    # Assert the number of portfolios retrieved
    assert len(portfolios) == 3

    # Assert the correct portfolios are retrieved
    assert any(p.name == "Tech Portfolio" and p.currency == "USD" for p in portfolios)
    assert any(p.name == "Growth Portfolio" and p.currency == "CAD" for p in portfolios)
    assert any(p.name == "Dividend Portfolio" and p.currency == "USD" for p in portfolios)
