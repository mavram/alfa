import random
import time

from alfa.db import BaseModel, Portfolio, open_db
from alfa.utils import get_current_utc_timestamp

if __name__ == "__main__":

    def get_external_id():
        return random.random() * 1000

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
            timestamp=get_current_utc_timestamp(),
            open=152.0,
            high=157.0,
            low=150.0,
            close=156.0,
            adjusted_close=155.5,
            volume=1100000,
        )
        # print(f"{aapl.symbol} has {len(aapl.prices)} price(s)")

        portfolio.deposit(get_external_id(), get_current_utc_timestamp(), 100)
        wait()
        portfolio.withdraw(get_external_id(), get_current_utc_timestamp(), 90)
        wait()
        portfolio.buy(get_external_id(), get_current_utc_timestamp(), "MSFT", 10, 1)
        wait()
        portfolio.deposit_in_kind(get_external_id(), get_current_utc_timestamp(), "MSFT", 100, 1)
        wait()
        portfolio.sell(get_external_id(), get_current_utc_timestamp(), "MSFT", 5, 2)
        wait()

        # for dw in portfolio.deposits_and_withdraws:
        #     print(f"{portfolio.name}: amount: {dw.amount}, type: {dw.type}")
        # for t in portfolio.transactions:
        #     print(f"{portfolio.name}: stock: {t.stock.symbol}, quantity: {t.quantity}, price: {t.price}, type: {t.type}")
        # for p in portfolio.positions:
        #     print(f"{portfolio.name}: stock: {p.stock.symbol}, size: {p.size}, average_price: {p.average_price}")

        portfolio.stop_watching("AAPL")
        portfolio.stop_watching("MSFT")

        # symbol = "MSFT"
        # portfolio.calculate_eod_position(symbol)
        # portfolio.get_most_recent_eod_position(symbol)

        # symbol = "TSLA"
        # portfolio.calculate_eod_position(symbol)
        # portfolio.get_most_recent_eod_position(symbol)

        db.close()
    except Exception as e:
        print(f"Exception: {e}")
