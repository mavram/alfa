import os

import pytest

from alfa.config import settings
from alfa.db import (
    BaseModel,
    CashLedger,
    CurrencyType,
    Portfolio,
    Position,
    Price,
    Stock,
    StockToWatch,
    TransactionLedger,
    TransactionType,
    _as_validated_symbol,
    open_db,
)


@pytest.fixture(scope="function")
def test_db():
    db = open_db()
    db.connect()
    db.create_tables(BaseModel.get_models())
    yield db  # Provides the initialized database to the test
    db.drop_tables(BaseModel.get_models())
    db.close()
    # Remove test database
    os.remove(settings.DB_PATH)


def test_as_validated_symbol_valid():
    symbol = "aapl"
    assert _as_validated_symbol(symbol) == "AAPL"


def test_as_validated_symbol_invalid_type():
    with pytest.raises(ValueError):
        _as_validated_symbol(123)


def test_as_validated_symbol_empty_string():
    with pytest.raises(ValueError):
        _as_validated_symbol("   ")


def test_create_stock(test_db):
    stock = Stock.create(id=1, symbol="AAPL", name="Apple Inc.")
    assert stock.symbol == "AAPL"
    assert stock.name == "Apple Inc."


def test_add_price(test_db):
    stock = Stock.create(id=1, symbol="AAPL", name="Apple Inc.")
    price = stock.add_price(
        timestamp=1638316800,
        open=150.0,
        high=155.0,
        low=149.0,
        close=154.0,
        adjusted_close=154.0,
        volume=1000000,
    )
    assert price.symbol == "AAPL"
    assert price.open == 150.0
    assert price.close == 154.0


def test_add_price_negative_volume(test_db):
    stock = Stock.create(id=1, symbol="AAPL", name="Apple Inc.")
    with pytest.raises(ValueError, match="Volume cannot be negative."):
        stock.add_price(
            timestamp=1638316800,
            open=150.0,
            high=155.0,
            low=149.0,
            close=154.0,
            adjusted_close=154.0,
            volume=-1000,  # Negative volume
        )


def test_get_most_recent_price(test_db):
    stock = Stock.create(id=1, symbol="AAPL", name="Apple Inc.")
    Price.create(
        stock=stock,
        symbol="AAPL",
        timestamp=1638316800,
        open=150.0,
        high=155.0,
        low=149.0,
        close=154.0,
        adjusted_close=154.0,
        volume=1000000,
    )
    Price.create(
        stock=stock,
        symbol="AAPL",
        timestamp=1638403200,
        open=155.0,
        high=160.0,
        low=154.0,
        close=158.0,
        adjusted_close=158.0,
        volume=1200000,
    )
    recent_price = stock.get_most_recent_price()
    assert recent_price.timestamp == 1638403200
    assert recent_price.close == 158.0


def test_get_most_recent_price_no_prices(test_db):
    stock = Stock.create(id=1, symbol="AAPL", name="Apple Inc.")
    recent_price = stock.get_most_recent_price()
    assert recent_price is None


def test_add_portfolio(test_db):
    portfolio = Portfolio.add_portfolio(name="My Portfolio", currency=CurrencyType.USD)
    assert portfolio.name == "My Portfolio"
    assert portfolio.currency == "USD"


def test_add_existing_portfolio(test_db):
    Portfolio.add_portfolio(name="My Portfolio", currency=CurrencyType.USD)
    portfolio = Portfolio.add_portfolio(name="My Portfolio")
    assert portfolio.name == "My Portfolio"
    assert portfolio.currency == "USD"


def test_get_portfolios(test_db):
    Portfolio.create(name="Portfolio 1", currency="USD")
    Portfolio.create(name="Portfolio 2", currency="CAD")
    portfolios = Portfolio.get_portfolios()
    assert len(portfolios) == 2
    names = {p.name for p in portfolios}
    assert "Portfolio 1" in names
    assert "Portfolio 2" in names


def test_is_watching_true(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD")
    stock = Stock.create(id=1, symbol="AAPL", name="Apple Inc.")
    StockToWatch.create(portfolio=portfolio, stock=stock)
    assert portfolio.is_watching("AAPL") is True


def test_is_watching_false(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD")
    assert portfolio.is_watching("AAPL") is False


def test_start_watching_new_stock(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD")
    stock = portfolio.start_watching(symbol="AAPL", name="Apple Inc.")
    assert stock.symbol == "AAPL"
    assert StockToWatch.select().where((StockToWatch.portfolio == portfolio) & (StockToWatch.stock == stock)).exists()


def test_start_watching_existing_stock(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD")
    Stock.create(id=1, symbol="AAPL", name="Apple Inc.")
    portfolio.start_watching(symbol="AAPL")
    portfolio.start_watching(symbol="AAPL")
    watchlist = StockToWatch.select().where(StockToWatch.portfolio == portfolio)
    assert watchlist.count() == 1


def test_stop_watching(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD")
    stock = Stock.create(id=1, symbol="AAPL", name="Apple Inc.")
    StockToWatch.create(portfolio=portfolio, stock=stock)
    portfolio.stop_watching("AAPL")
    assert not StockToWatch.select().where((StockToWatch.portfolio == portfolio) & (StockToWatch.stock == stock)).exists()


def test_stop_watching_unknown_stock(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD")
    portfolio.stop_watching("AAPL")
    assert True


def test_deposit(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD", cash=1000.0)
    portfolio.deposit(external_id="dep1", timestamp=1638316800, amount=500.0, fees=10.0)
    assert portfolio.cash == 1490.0
    ledger = CashLedger.get(CashLedger.external_id == "dep1")
    assert ledger.amount == 490.0
    assert ledger.type == TransactionType.DEPOSIT.value


def test_withdraw(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD", cash=1000.0)
    portfolio.withdraw(external_id="wd1", timestamp=1638316800, amount=200.0, fees=5.0)
    assert portfolio.cash == 795.0
    ledger = CashLedger.get(CashLedger.external_id == "wd1")
    assert ledger.amount == -200.0
    assert ledger.type == TransactionType.WITHDRAW.value


def test_withdraw_exceeds_balance(test_db):
    # Create a Portfolio with an initial cash balance of $1,000.00
    portfolio = Portfolio.create(name="Test Portfolio", currency="USD", cash=1000.0)

    # Attempt to withdraw $900.00 with $200.00 in fees, totaling $1,100.00
    with pytest.raises(ValueError):
        portfolio.withdraw(external_id="wd_exceed1", timestamp=1638316800, amount=900.0, fees=200.0)

    # Assert that the cash balance is now $0.00
    assert portfolio.cash == 1000.0, f"Expected cash balance to be $1000.00, got ${portfolio.cash}"


def test_buy_insufficient_cash(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD", cash=100.0)
    with pytest.raises(ValueError):
        portfolio.buy(external_id="buy1", timestamp=1638316800, symbol="AAPL", quantity=10, price=15.0, fees=10.0)


def test_buy_successful(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD", cash=1000.0)
    portfolio.buy(external_id="buy1", timestamp=1638316800, symbol="AAPL", quantity=10, price=50.0, fees=10.0)
    assert portfolio.cash == 1000.0 - (10 * 50.0 + 10.0)
    position = Position.select().join(Stock).where((Position.portfolio == portfolio) & (Stock.symbol == "AAPL")).get()
    assert position.size == 10
    assert position.average_price == 50.0
    transaction = TransactionLedger.get(TransactionLedger.external_id == "buy1")
    assert transaction.quantity == 10
    assert transaction.price == 50.0
    assert transaction.type == TransactionType.BUY.value


def test_sell_no_position(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD", cash=1000.0)
    with pytest.raises(ValueError):
        portfolio.sell(external_id="sell1", timestamp=1638316800, symbol="AAPL", quantity=5, price=55.0, fees=5.0)


def test_sell_successful(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD", cash=1000.0)
    stock = Stock.create(id=1, symbol="AAPL", name="Apple Inc.")
    Position.create(portfolio=portfolio, stock=stock, size=10, average_price=50.0)
    portfolio.sell(external_id="sell1", timestamp=1638316800, symbol="AAPL", quantity=5, price=55.0, fees=5.0)
    assert portfolio.cash == 1000.0 + (5 * 55.0 - 5.0)
    position = Position.get((Position.portfolio == portfolio) & (Position.stock == stock))
    assert position.size == 5
    assert position.average_price == 50.0
    transaction = TransactionLedger.get(TransactionLedger.external_id == "sell1")
    assert transaction.quantity == -5
    assert transaction.price == 55.0
    assert transaction.type == TransactionType.SELL.value


def test_sell_entire_position(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD", cash=1000.0)
    stock = Stock.create(id=1, symbol="AAPL", name="Apple Inc.")
    Position.create(portfolio=portfolio, stock=stock, size=10, average_price=50.0)
    portfolio.sell(external_id="sell2", timestamp=1638316800, symbol="AAPL", quantity=10, price=55.0, fees=5.0)
    assert portfolio.cash == 1000.0 + (10 * 55.0 - 5.0)
    with pytest.raises(Position.DoesNotExist):
        Position.get((Position.portfolio == portfolio) & (Position.stock == stock))
    assert not StockToWatch.select().where((StockToWatch.portfolio == portfolio) & (StockToWatch.stock == stock)).exists()
    transaction = TransactionLedger.get(TransactionLedger.external_id == "sell2")
    assert transaction.quantity == -10
    assert transaction.type == TransactionType.SELL.value


def test_sell_quantity_exceeds_position_size(test_db):
    # Create a Portfolio with an initial cash balance of $1,000.00
    portfolio = Portfolio.create(name="Test Portfolio", currency="USD", cash=1000.0)

    # Create a Stock with symbol "AAPL"
    stock = Stock.create(id=1, symbol="AAPL", name="Apple Inc.")

    # Create a Position for the Portfolio in "AAPL" with size 5 and average price $50.00
    Position.create(portfolio=portfolio, stock=stock, size=5, average_price=50.0)

    # Add "AAPL" to the Portfolio's watchlist
    StockToWatch.create(portfolio=portfolio, stock=stock)

    # Attempt to sell 10 shares of "AAPL" with a price of $55.00 per share and $5.00 in fees
    with pytest.raises(ValueError):
        portfolio.sell(
            external_id="sell_exceed1",
            timestamp=1638316800,  # Example Unix timestamp
            symbol="AAPL",
            quantity=10,  # Quantity exceeds position size (5)
            price=55.0,
            fees=5.0,
        )

    # Re-fetch the Portfolio to verify the cash balance
    portfolio = Portfolio.get_by_id(portfolio.id)
    assert portfolio.cash == 1000.0, f"Expected cash balance to be $1000.00, got ${portfolio.cash}"


def test_deposit_in_kind_insufficient_cash(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD", cash=5.0)
    with pytest.raises(ValueError):
        portfolio.deposit_in_kind(
            external_id="dik1",
            timestamp=1638316800,
            symbol="AAPL",
            quantity=10,
            cost_basis_per_share=50.0,
            fees=10.0,
        )


def test_deposit_in_kind_successful(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD", cash=1000.0)
    portfolio.deposit_in_kind(
        external_id="dik1",
        timestamp=1638316800,
        symbol="AAPL",
        quantity=10,
        cost_basis_per_share=50.0,
        fees=10.0,
    )
    assert portfolio.cash == 1000.0 - 10.0
    position = Position.select().join(Stock).where((Position.portfolio == portfolio) & (Stock.symbol == "AAPL")).get()
    assert position.size == 10
    assert position.average_price == 50.0
    transaction = TransactionLedger.get(TransactionLedger.external_id == "dik1")
    assert transaction.quantity == 10
    assert transaction.type == TransactionType.DEPOSIT_IN_KIND.value


def test_get_watchlist(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD")
    stock1 = Stock.create(id=1, symbol="AAPL", name="Apple Inc.")
    stock2 = Stock.create(id=2, symbol="GOOGL", name="Alphabet Inc.")
    StockToWatch.create(portfolio=portfolio, stock=stock1)
    StockToWatch.create(portfolio=portfolio, stock=stock2)
    watchlist = portfolio.get_watchlist()
    symbols = {stock.symbol for stock in watchlist}
    assert symbols == {"AAPL", "GOOGL"}


def test_get_position_nonexistent(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD")
    position = portfolio.get_position("AAPL")
    assert position is None


def test_get_position_existing(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD")
    stock = Stock.create(id=1, symbol="AAPL", name="Apple Inc.")
    Position.create(portfolio=portfolio, stock=stock, size=10, average_price=50.0)
    position = portfolio.get_position("AAPL")
    assert position.size == 10
    assert position.average_price == 50.0


def test_stop_watching_with_active_position(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD")
    stock = Stock.create(id=1, symbol="AAPL", name="Apple Inc.")
    StockToWatch.create(portfolio=portfolio, stock=stock)
    Position.create(portfolio=portfolio, stock=stock, size=10, average_price=50.0)
    portfolio.stop_watching("AAPL")
    assert StockToWatch.select().where((StockToWatch.portfolio == portfolio) & (StockToWatch.stock == stock)).exists()


def test_stop_watching_without_position(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD")
    stock = Stock.create(id=1, symbol="AAPL", name="Apple Inc.")
    StockToWatch.create(portfolio=portfolio, stock=stock)
    portfolio.stop_watching("AAPL")
    assert not StockToWatch.select().where((StockToWatch.portfolio == portfolio) & (StockToWatch.stock == stock)).exists()


def test_create_or_update_position_addition(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD")
    Stock.create(id=1, symbol="AAPL", name="Apple Inc.")
    position = portfolio._create_or_update_position("AAPL", 10, 50.0)
    assert position.size == 10
    assert position.average_price == 50.0


def test_create_or_update_position_removal(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD")
    stock = Stock.create(id=1, symbol="AAPL", name="Apple Inc.")
    Position.create(portfolio=portfolio, stock=stock, size=10, average_price=50.0)
    position = portfolio._create_or_update_position("AAPL", -10, 50.0)
    assert position is None
    with pytest.raises(Position.DoesNotExist):
        Position.get((Position.portfolio == portfolio) & (Position.stock == stock))


def test_create_or_update_position_negative_size(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD")
    stock = Stock.create(id=1, symbol="AAPL", name="Apple Inc.")
    Position.create(portfolio=portfolio, stock=stock, size=5, average_price=50.0)
    with pytest.raises(ValueError):
        portfolio._create_or_update_position("AAPL", -10, 50.0)


def test_create_or_update_position_average_price_update(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD")
    stock = Stock.create(id=1, symbol="AAPL", name="Apple Inc.")
    Position.create(portfolio=portfolio, stock=stock, size=10, average_price=50.0)
    portfolio._create_or_update_position("AAPL", 10, 60.0)
    position = Position.get((Position.portfolio == portfolio) & (Position.stock == stock))
    assert position.size == 20
    assert position.average_price == 55.0


def test_transaction_ledgers_unique_external_id(test_db):
    portfolio = Portfolio.create(name="Portfolio", currency="USD")
    stock = Stock.create(id=1, symbol="AAPL", name="Apple Inc.")
    TransactionLedger.create(
        external_id="tx1",
        portfolio=portfolio,
        timestamp=1638316800,
        stock=stock,
        quantity=10,
        price=50.0,
        type=TransactionType.BUY.value,
        fees=10.0,
    )
    with pytest.raises(Exception):
        TransactionLedger.create(
            external_id="tx1",
            portfolio=portfolio,
            timestamp=1638316801,
            stock=stock,
            quantity=5,
            price=55.0,
            type=TransactionType.SELL.value,
            fees=5.0,
        )
