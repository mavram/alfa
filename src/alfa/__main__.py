import random
from datetime import datetime

from alfa.db import BaseModel, Portfolio, open_db

if __name__ == "__main__":

    def get_external_id():
        return random.random() * 1000

    def get_timestamp(day, hour, minute):
        return datetime(2024, 12, day, hour, minute).timestamp() * 1000

    try:
        db = open_db()
        db.connect()
        db.create_tables(BaseModel.get_models())

        portfolio = Portfolio.initialize("Theta")
        tsla = portfolio.start_watching("TSLA")

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

        portfolio.deposit(get_external_id(), get_timestamp(2, 11, 11), 10000)
        portfolio.withdraw(get_external_id(), get_timestamp(3, 12, 12), 1000)
        portfolio.buy(get_external_id(), get_timestamp(3, 13, 13), "tsla", 5, 400)
        portfolio.deposit_in_kind(get_external_id(), get_timestamp(4, 11, 11), "tsla", 100, 200)
        portfolio.sell(get_external_id(), get_timestamp(4, 15, 15), "TSLA", 100, 500)
        portfolio.buy(get_external_id(), get_timestamp(5, 10, 10), "nvda", 10, 200)

        portfolio.get_eod_position("TSLA")
        portfolio.get_eod_position("NVDA")
        portfolio.get_eod_balance()

        watchlist = portfolio.get_watchlist()
        print("Portfolio Watchlist:")
        _ = [print(f"id: {s.id}, symbol: {s.symbol}, name: {s.name}") for s in watchlist]

        db.close()
    except Exception as e:
        print(f"Exception: {e}")
