from alfa.db import CashLedger, CurrencyType, Portfolio, Stock, TransactionType
from alfa.util import get_current_utc_timestamp


def test_add_portfolio(setup_database):
    portfolio = Portfolio.add_portfolio("__theta__", CurrencyType.USD)
    assert portfolio is not None
    assert portfolio.name == "__theta__"
    assert portfolio.currency == "USD"

    # Attempt to add duplicate portfolio
    duplicate_portfolio = Portfolio.add_portfolio("__theta__", CurrencyType.USD)
    assert duplicate_portfolio is None  # Should fail due to unique constraint


def test_start_watching(setup_database):
    # Create portfolio and stock
    portfolio = Portfolio.add_portfolio("__theta__", CurrencyType.USD)
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

    # Add stock that is not in stocks to watchlist
    added = portfolio.start_watching("TSLA")
    assert added is True


def test_stop_watching(setup_database):
    # Create portfolio and stock
    portfolio = Portfolio.add_portfolio("__theta__", CurrencyType.USD)
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
    portfolio = Portfolio.add_portfolio("__theta__", CurrencyType.CAD)
    assert portfolio.get_currency() == CurrencyType.CAD

    portfolio_usd = Portfolio.add_portfolio("Growth Portfolio", CurrencyType.USD)
    assert portfolio_usd.get_currency() == CurrencyType.USD


def test_get_portfolios(setup_database):
    # Add portfolios
    Portfolio.add_portfolio("Tech Portfolio", CurrencyType.USD)
    Portfolio.add_portfolio("Growth Portfolio", CurrencyType.CAD)
    Portfolio.add_portfolio("Dividend Portfolio", CurrencyType.USD)

    # Retrieve portfolios
    portfolios = Portfolio.get_portfolios()

    # Assert the number of portfolios retrieved
    assert len(portfolios) == 3

    # Assert the correct portfolios are retrieved
    assert any(p.name == "Tech Portfolio" and p.currency == "USD" for p in portfolios)
    assert any(p.name == "Growth Portfolio" and p.currency == "CAD" for p in portfolios)
    assert any(p.name == "Dividend Portfolio" and p.currency == "USD" for p in portfolios)


def test_deposit(setup_database):
    # Create a portfolio
    portfolio = Portfolio.add_portfolio(name="Test Portfolio", currency=CurrencyType.USD)
    assert portfolio is not None

    # Initial cash balance should be 0.0
    assert portfolio.cash == 0.0

    # Perform a deposit
    amount = 1000.0
    external_id = 1
    timestamp = get_current_utc_timestamp()
    result = portfolio.deposit(external_id, amount, timestamp)
    assert result is True

    # Reload the portfolio from the database to get updated values
    portfolio_from_db = Portfolio.get(Portfolio.id == portfolio.id)
    assert portfolio_from_db.cash == amount

    # Check that a CashLedger entry was created
    cash_ledger_entry = CashLedger.get(CashLedger.external_id == external_id)
    assert cash_ledger_entry.amount == amount
    assert cash_ledger_entry.type == TransactionType.DEPOSIT.value
    assert cash_ledger_entry.portfolio.id == portfolio.id
    assert cash_ledger_entry.timestamp == timestamp


def test_withdraw(setup_database):
    # Create a portfolio with an initial cash balance
    portfolio = Portfolio.add_portfolio(name="Test Portfolio", currency=CurrencyType.USD)
    assert portfolio is not None

    # Deposit some initial cash
    deposit_amount = 1000.0
    deposit_external_id = 1
    deposit_timestamp = get_current_utc_timestamp()
    portfolio.deposit(deposit_external_id, deposit_amount, deposit_timestamp)

    # Perform a withdrawal
    withdraw_amount = 500.0
    withdraw_external_id = 2
    withdraw_timestamp = get_current_utc_timestamp()
    result = portfolio.withdraw(withdraw_external_id, withdraw_amount, withdraw_timestamp)
    assert result is True

    # Reload the portfolio from the database to get updated values
    portfolio_from_db = Portfolio.get(Portfolio.id == portfolio.id)
    assert portfolio_from_db.cash == deposit_amount - withdraw_amount

    # Check that a CashLedger entry was created
    cash_ledger_entry = CashLedger.get(CashLedger.external_id == withdraw_external_id)
    assert cash_ledger_entry.amount == -withdraw_amount
    assert cash_ledger_entry.type == TransactionType.WITHDRAW.value
    assert cash_ledger_entry.portfolio.id == portfolio.id
    assert cash_ledger_entry.timestamp == withdraw_timestamp


def test_withdraw_exceeds_cash(setup_database):
    # Create a portfolio with an initial cash balance
    portfolio = Portfolio.add_portfolio(name="Test Portfolio", currency=CurrencyType.USD)
    assert portfolio is not None

    # Deposit some initial cash
    deposit_amount = 500.0
    deposit_external_id = 1
    deposit_timestamp = get_current_utc_timestamp()
    portfolio.deposit(deposit_external_id, deposit_amount, deposit_timestamp)

    # Attempt to withdraw more than the available cash
    withdraw_amount = 1000.0  # Exceeds available cash
    withdraw_external_id = 2
    withdraw_timestamp = get_current_utc_timestamp()
    result = portfolio.withdraw(withdraw_external_id, withdraw_amount, withdraw_timestamp)
    assert result is True

    # Reload the portfolio from the database to get updated values
    portfolio_from_db = Portfolio.get(Portfolio.id == portfolio.id)
    assert portfolio_from_db.cash == 0.0  # Cash should be depleted

    # Check that a CashLedger entry was created with the capped amount
    cash_ledger_entry = CashLedger.get(CashLedger.external_id == withdraw_external_id)
    assert cash_ledger_entry.amount == -deposit_amount  # Only the available cash was withdrawn
    assert cash_ledger_entry.type == TransactionType.WITHDRAW.value
    assert cash_ledger_entry.portfolio.id == portfolio.id
    assert cash_ledger_entry.timestamp == withdraw_timestamp


def test_multiple_deposits_and_withdrawals(setup_database):
    # Create a portfolio
    portfolio = Portfolio.add_portfolio(name="Test Portfolio", currency=CurrencyType.USD)
    assert portfolio is not None

    # First deposit
    amount1 = 1000.0
    external_id1 = 1
    timestamp1 = get_current_utc_timestamp()
    portfolio.deposit(external_id1, amount1, timestamp1)

    # Second deposit
    amount2 = 500.0
    external_id2 = 2
    timestamp2 = get_current_utc_timestamp()
    portfolio.deposit(external_id2, amount2, timestamp2)

    # First withdrawal
    withdraw_amount1 = 300.0
    withdraw_external_id1 = 3
    withdraw_timestamp1 = get_current_utc_timestamp()
    portfolio.withdraw(withdraw_external_id1, withdraw_amount1, withdraw_timestamp1)

    # Second withdrawal
    withdraw_amount2 = 800.0
    withdraw_external_id2 = 4
    withdraw_timestamp2 = get_current_utc_timestamp()
    portfolio.withdraw(withdraw_external_id2, withdraw_amount2, withdraw_timestamp2)

    # Expected cash balance
    expected_cash = amount1 + amount2 - withdraw_amount1 - withdraw_amount2
    if expected_cash < 0:
        expected_cash = 0.0  # Since withdrawals cannot exceed cash balance

    # Reload the portfolio from the database to get updated values
    portfolio_from_db = Portfolio.get(Portfolio.id == portfolio.id)
    assert portfolio_from_db.cash == expected_cash

    # Check the number of CashLedger entries
    ledger_entries = CashLedger.select().where(CashLedger.portfolio == portfolio)
    assert ledger_entries.count() == 4


def test_deposit_with_duplicate_external_id(setup_database):
    # Create a portfolio
    portfolio = Portfolio.add_portfolio(name="Test Portfolio", currency=CurrencyType.USD)
    assert portfolio is not None

    # Perform a deposit
    amount = 1000.0
    external_id = 1
    timestamp = get_current_utc_timestamp()
    result = portfolio.deposit(external_id, amount, timestamp)
    assert result is True

    # Attempt to perform another deposit with the same external_id
    amount2 = 500.0
    result2 = portfolio.deposit(external_id, amount2, timestamp)
    assert result2 is False

    # Check that the cash balance did not increase by the second amount
    portfolio_from_db = Portfolio.get(Portfolio.id == portfolio.id)
    assert portfolio_from_db.cash == amount  # Only the first deposit amount

    # Only one CashLedger entry should exist with the external_id
    ledger_entries = CashLedger.select().where(CashLedger.portfolio == portfolio)
    assert ledger_entries.count() == 1


def test_withdraw_with_duplicate_external_id(setup_database):
    # Create a portfolio with an initial cash balance
    portfolio = Portfolio.add_portfolio(name="Test Portfolio", currency=CurrencyType.USD)
    assert portfolio is not None

    # Deposit initial cash
    deposit_amount = 1000.0
    deposit_external_id = 1
    deposit_timestamp = get_current_utc_timestamp()
    portfolio.deposit(deposit_external_id, deposit_amount, deposit_timestamp)

    # Perform a withdrawal
    withdraw_amount = 500.0
    external_id = 2
    timestamp = get_current_utc_timestamp()
    result = portfolio.withdraw(external_id, withdraw_amount, timestamp)
    assert result is True

    # Attempt to perform another withdrawal with the same external_id
    withdraw_amount2 = 300.0
    result2 = portfolio.withdraw(external_id, withdraw_amount2, timestamp)
    assert result2 is False

    # Check that the cash balance did not decrease by the second amount
    portfolio_from_db = Portfolio.get(Portfolio.id == portfolio.id)
    assert portfolio_from_db.cash == deposit_amount - withdraw_amount

    # Only one CashLedger entry should exist with the external_id
    ledger_entries = CashLedger.select().where(CashLedger.portfolio == portfolio)
    assert ledger_entries.count() == 2  # One deposit and one withdrawal
