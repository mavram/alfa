import random
import time
from datetime import date, datetime, timezone

from alfa.db import BaseModel, Portfolio, open_db

if __name__ == "__main__":

    def get_external_id():
        return random.random() * 1000

    def get_now_timestamp():
        return int(datetime.now().timestamp() * 1000)  # convert to milliseconds

    def wait():
        time.sleep(0.001)  # wait one ms

    try:
        db = open_db()
        db.connect()
        db.create_tables(BaseModel.get_models())

        portfolio = Portfolio.add_portfolio("Theta")

        aapl = portfolio.start_watching("AAPL", "Apple Inc.")
        tsla = portfolio.start_watching("TSLA")

        aapl.add_price(
            timestamp=get_now_timestamp(),
            open=152.0,
            high=157.0,
            low=150.0,
            close=156.0,
            adjusted_close=155.5,
            volume=1100000,
        )

        portfolio.deposit(get_external_id(), get_now_timestamp(), 100)
        wait()
        portfolio.withdraw(get_external_id(), get_now_timestamp(), 90)
        wait()
        portfolio.buy(get_external_id(), get_now_timestamp(), "MSFT", 10, 1)
        wait()
        portfolio.deposit_in_kind(get_external_id(), get_now_timestamp(), "MSFT", 100, 1)
        wait()
        portfolio.sell(get_external_id(), get_now_timestamp(), "MSFT", 5, 2)
        wait()

        portfolio.stop_watching("AAPL")
        portfolio.stop_watching("MSFT")

        portfolio.get_eod_balance()

        portfolio.get_eod_position("MSFT")
        portfolio.get_eod_position("TSLA")

        db.close()
    except Exception as e:
        print(f"Exception: {e}")
