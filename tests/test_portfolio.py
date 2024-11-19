import pytest

from alfa.portfolio import Portfolio


@pytest.fixture
def p():
    return Portfolio("Test")


def test_get_positions(p):
    assert p.get_positions() == []


def test_get_positions_with_two_symbols(p):
    p.deposit(1000)
    p.buy("AAPL", 2, 100)
    p.buy("TSLA", 3, 100)

    positions = p.get_positions()

    assert len(positions) == 2
    assert "AAPL" in positions
    assert "TSLA" in positions


def test_get_position_size_empty(p):
    # Test get_position_size for a symbol that doesn't exist
    assert p.get_position_size("AAPL") == 0


def test_get_cash(p):
    assert p.get_cash() == 0


def test_buy_insufficient_cash(p):
    p.deposit(100)
    result = p.buy("AAPL", 10, 150)

    assert result is False
    assert p.get_position_size("AAPL") == 0
    assert p.get_cash() == 100


def test_deposit_cash(p):
    p.deposit(1000)
    assert p.get_cash() == 1000


def test_withdraw_cash(p):
    p.deposit(1000)
    p.withdraw(500)
    assert p.get_cash() == 500


def test_withdraw_cash_insufficient_funds(p):
    p.deposit(500)
    p.withdraw(1000)
    assert p.get_cash() == 0


def test_buy_stock(p):
    p.deposit(1000)
    p.buy("AAPL", 2, 100)
    assert p.get_position_size("AAPL") == 2
    assert p.get_cash() == 800
    assert p.positions["AAPL"]["average_price"] == 100


def test_buy_stock_insufficient_cash(p):
    p.deposit(100)
    success = p.buy("AAPL", 2, 100)
    assert success is False
    assert p.get_position_size("AAPL") == 0
    assert p.get_cash() == 100


def test_sell_stock(p):
    p.deposit(1000)
    p.buy("AAPL", 5, 100)
    p.sell("AAPL", 3, 150)
    assert p.get_position_size("AAPL") == 2
    assert p.get_cash() == 1000 + (3 * 150) - (5 * 100)  # Remaining balance after buy and sell


def test_sell_stock_not_owned(p):
    success = p.sell("AAPL", 2, 150)
    assert success is False
    assert p.get_position_size("AAPL") == 0


def test_sell_stock_partial_liquidation(p):
    p.deposit(1000)
    p.buy("AAPL", 5, 100)
    p.sell("AAPL", 2, 150)
    assert p.get_position_size("AAPL") == 3
    assert p.get_cash() == 1000 + (2 * 150) - (5 * 100)


def test_sell_stock_full_liquidation(p):
    p.deposit(1000)
    p.buy("AAPL", 5, 100)
    p.sell("AAPL", 5, 150)
    assert "AAPL" not in p.get_positions()
    assert p.get_cash() == 1000 + (5 * 150) - (5 * 100)


def test_sell_stock_full_liquidation_due_to_cap(p):
    p.deposit(1000)
    p.buy("AAPL", 5, 100)
    p.sell("AAPL", 10, 150)
    assert "AAPL" not in p.get_positions()
    assert p.get_cash() == 1000 + (5 * 150) - (5 * 100)


def test_get_position_size_case_insensitive(p):
    p.deposit(1000)
    p.buy("AAPL", 5, 100)
    assert p.get_position_size("aapl") == 5
    assert p.get_position_size("AAPL") == 5


def test_deposit_stock(p):
    p.deposit_stock("AAPL", 10, 120, 23)
    assert p.get_position_size("AAPL") == 10


def test_start_watching(p):
    p.start_watching("AAPL")
    p.start_watching("GOOG")
    assert "AAPL" in p.get_stocks_to_watch()
    assert "GOOG" in p.get_stocks_to_watch()
    assert len(p.get_stocks_to_watch()) == 2


def test_start_watching_duplicate(p):
    p.start_watching("AAPL")
    p.start_watching("AAPL")
    assert p.get_stocks_to_watch() == ["AAPL"]
    assert len(p.get_stocks_to_watch()) == 1


def test_stop_watching(p):
    p.start_watching("AAPL")
    p.start_watching("GOOG")
    p.stop_watching("AAPL")
    assert "AAPL" not in p.get_stocks_to_watch()
    assert "GOOG" in p.get_stocks_to_watch()
    assert len(p.get_stocks_to_watch()) == 1


def test_stop_watching_not_in_list(p):
    p.start_watching("AAPL")
    p.stop_watching("GOOG")
    assert "AAPL" in p.get_stocks_to_watch()
    assert len(p.get_stocks_to_watch()) == 1


def test_get_stocks_to_watch_empty(p):
    assert p.get_stocks_to_watch() == []
