from datetime import date, datetime

from peewee import IntegrityError

from alfa.config import log
from alfa.db import BaseModel, CurrencyType, Portfolio, open_db

if __name__ == "__main__":

    def get_timestamp(day, hour, minute):
        return int(datetime(2024, 12, day, hour, minute).timestamp() * 1000)

    try:
        db = open_db()
        db.connect()
        db.create_tables(BaseModel.get_models())

        portfolio = Portfolio.init("Theta")

        portfolio.add_account("TFSA", CurrencyType.USD)
        portfolio.add_account("TFSA", CurrencyType.CAD)
        print("Portfolio Accounts:")
        for a in portfolio.get_accounts():
            print(f"name: {a.name}, currency: {a.currency}")

        tsla = portfolio.start_watching("TSLA")

        try:
            tsla.add_price(
                timestamp=get_timestamp(2, 16, 00),
                open=152.0,
                high=157.0,
                low=150.0,
                close=156.0,
                adjusted_close=400.0,
                volume=1100000,
            )
            tsla.add_price(
                timestamp=get_timestamp(3, 16, 00),
                open=156.0,
                high=157.0,
                low=150.0,
                close=157.0,
                adjusted_close=450.0,
                volume=1100000,
            )
            tsla.add_price(
                timestamp=get_timestamp(4, 16, 00),
                open=156.0,
                high=157.0,
                low=150.0,
                close=157.0,
                adjusted_close=500.0,
                volume=1100000,
            )
        except IntegrityError as e:
            print(f"{type(e).__name__} : {e}")

        tsla.get_eod_price()
        tsla.get_eod_price(date(2024, 12, 2))
        tsla.get_eod_price(date(2024, 12, 4))

        tfsa_usd = portfolio.get_account("TFSA", CurrencyType.USD)

        try:
            tfsa_usd.deposit(1, get_timestamp(2, 11, 11), 10000)
            tfsa_usd.withdraw(2, get_timestamp(3, 12, 12), 1000)
            tfsa_usd.buy(3, get_timestamp(3, 13, 13), "tsla", 5, 400)
            tfsa_usd.deposit_in_kind(4, get_timestamp(4, 11, 11), "tsla", 100, 200)
            tfsa_usd.sell(5, get_timestamp(4, 15, 15), "TSLA", 100, 500)
            tfsa_usd.buy(6, get_timestamp(5, 10, 10), "nvda", 10, 200)
        except IntegrityError as e:
            print(f"{type(e).__name__} : {e}")

        tfsa_usd.get_cash()
        tfsa_usd.get_position("TSLA")
        tfsa_usd.get_position("NVDA")
        tfsa_usd.get_position("MSFT")

        tfsa_usd.get_eod_position("TSLA")
        tfsa_usd.get_eod_position("NVDA")
        tfsa_usd.get_eod_balance()

        watchlist = portfolio.get_watchlist()
        print("Portfolio Watchlist:")
        _ = [print(f"id: {s.id}, symbol: {s.symbol}, name: {s.name}") for s in watchlist]

        db.close()
    except Exception as e:
        print(f"{type(e).__name__} : {e}")
        log.exception(e)
