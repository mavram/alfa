import pytest
from unittest.mock import patch, MagicMock
from alfa.portfolio import Portfolio

@pytest.fixture
def mock_settings():
    # Mock settings.PORTFOLIO_NAME
    with patch("portfolio.settings") as mock_settings:
        mock_settings.PORTFOLIO_NAME = "DefaultPortfolio"
        yield mock_settings

@pytest.fixture
def mock_logger():
    # Mock the logger
    with patch("portfolio.get_logger") as mock_logger:
        mock_logger.return_value = MagicMock()
        yield mock_logger

@pytest.fixture
def portfolio(mock_settings):
    # Create a Portfolio instance for testing
    return Portfolio()

def test_portfolio_initialization(mock_settings, portfolio):
    # Test that the portfolio is initialized correctly
    assert portfolio.name == "DefaultPortfolio"
    assert portfolio.cash == 0
    assert portfolio.positions == {}
    assert portfolio.stocks_to_watch == []

def test_get_all_positions(portfolio):
    # Test get_all_positions method
    assert portfolio.get_all_positions() == {}

def test_get_position_size_empty(portfolio):
    # Test get_position_size for a symbol that doesn't exist
    assert portfolio.get_position_size("AAPL") == 0

def test_get_position_size_with_position(portfolio):
    # Add a position and test get_position_size
    portfolio.positions = {"AAPL": {"size": 100, "average_price": 150.0}}
    assert portfolio.get_position_size("AAPL") == {"size": 100, "average_price": 150.0}

def test_get_cash_balance(portfolio):
    # Test get_cash_balance method
    assert portfolio.get_cash_balance() == 0

def test_buy_new_position(mock_logger, portfolio):
    # Test buying a new stock
    portfolio.buy("AAPL", 10, 150.0)
    assert portfolio.positions["AAPL"]["size"] == 10
    assert portfolio.positions["AAPL"]["average_price"] == 150.0
    mock_logger.return_value.info.assert_called_with("Transaction - BUY 10 AAPL @ 150.0")

def test_buy_existing_position(mock_logger, portfolio):
    # Test buying more of an existing stock
    portfolio.positions = {"AAPL": {"size": 10, "average_price": 150.0}}
    portfolio.buy("AAPL", 10, 200.0)
    assert portfolio.positions["AAPL"]["size"] == 20
    assert portfolio.positions["AAPL"]["average_price"] == 175.0
    mock_logger.return_value.info.assert_called_with("Transaction - BUY 10 AAPL @ 200.0")

def test_sell_full_position(mock_logger, portfolio):
    # Test selling a full position
    portfolio.positions = {"AAPL": {"size": 10, "average_price": 150.0}}
    portfolio.sell("AAPL", 10, 200.0)
    assert "AAPL" not in portfolio.positions
    assert portfolio.cash == 2000.0
    mock_logger.return_value.info.assert_called_with("Transaction - SELL 10 AAPL @ 200.0")

def test_sell_partial_position(mock_logger, portfolio):
    # Test selling part of a position
    portfolio.positions = {"AAPL": {"size": 10, "average_price": 150.0}}
    portfolio.sell("AAPL", 5, 200.0)
    assert portfolio.positions["AAPL"]["size"] == 5
    assert portfolio.cash == 1000.0
    mock_logger.return_value.info.assert_called_with("Transaction - SELL 5 AAPL @ 200.0")

def test_sell_no_position(mock_logger, portfolio):
    # Test selling a stock not in the portfolio
    assert not portfolio.sell("AAPL", 10, 200.0)
    mock_logger.return_value.error.assert_called_with("Portfolio DefaultPortfolio has no position in AAPL.")