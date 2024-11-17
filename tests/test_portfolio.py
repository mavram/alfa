import pytest
from alfa.portfolio import Portfolio


@pytest.fixture
def portfolio():
    return Portfolio("Test")


def test_get_all_positions(portfolio):
    assert portfolio.get_all_positions() == {}


def test_get_position_size_empty(portfolio):
    # Test get_position_size for a symbol that doesn't exist
    assert portfolio.get_position_size("AAPL") == 0


def test_get_cash(portfolio):
    assert portfolio.get_cash() == 0


def test_buy_insufficient_cash(portfolio):
    portfolio.deposit(100)
    result = portfolio.buy("AAPL", 10, 150)

    assert result is False
    assert portfolio.get_position_size("AAPL") == 0
    assert portfolio.get_cash() == 100
