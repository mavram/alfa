import pytest
from alfa.portfolio import Portfolio

@pytest.fixture
def portfolio():
    # Create a Portfolio instance for testing
    return Portfolio("Test")

def test_get_all_positions(portfolio):
    # Test get_all_positions method
    assert portfolio.get_all_positions() == {}

def test_get_position_size_empty(portfolio):
    # Test get_position_size for a symbol that doesn't exist
    assert portfolio.get_position_size("AAPL") == 0

def test_get_cash_balance(portfolio):
    # Test get_cash_balance method
    assert portfolio.get_cash_balance() == 0

# def test_get_position_size_with_position(portfolio):
#     # Add a position and test get_position_size
#     portfolio.buy("AAPL", 10, 120)
#     assert portfolio.get_position_size("AAPL") == 10
