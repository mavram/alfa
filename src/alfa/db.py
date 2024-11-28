# CREATE TABLE IF NOT EXISTS stock (
#     id INTEGER PRIMARY KEY,
#     symbol TEXT NOT NULL UNIQUE,
#     name TEXT NOT NULL
#     );

# CREATE TABLE IF NOT EXISTS price (
#     id INTEGER PRIMARY KEY,
#     stock_id INTEGER,
#     date NOT NULL,
#     open NOT NULL,
#     high NOT NULL,
#     low NOT NULL,
#     close NOT NULL,
#     adjusted_close NOT NULL,
#     volume NOT NULL,
#     FOREIGN KEY (stock_id) REFERENCES stock (id)
#     );

# CREATE TABLE IF NOT EXISTS portfolio (
#     id INTEGER PRIMARY KEY,
#     name TEXT NOT NULL UNIQUE,
#     currency TEXT NOT NULL UNIQUE
#     );

# CREATE TABLE IF NOT EXISTS stock_to_watch (
#     id INTEGER PRIMARY KEY,
#     stock_id INTEGER,
#     symbol TEXT NOT NULL UNIQUE,
#     portfolio_id INTEGER,
#     FOREIGN KEY (portfolio_id) REFERENCES portfolio (id),
#     FOREIGN KEY (stock_id) REFERENCES stock (id)
#     );

# CREATE TABLE IF NOT EXISTS transaction_ledger (
#     id INTEGER PRIMARY KEY,
#     external_id INTEGER NOT NULL UNIQUE,
#     portfolio_id INTEGER,
#     timestamp INTEGER NOT NULL,
#     stock_id INTEGER,
#     quantity NOT NULL,
#     price NOT NULL,
#     type NOT NULL, -- BUY, SELL, DEPOSIT_STOCK
#     fees NOT NULL,
#     FOREIGN KEY (portfolio_id) REFERENCES portfolio (id),
#     FOREIGN KEY (stock_id) REFERENCES stock (id)
#     );

# CREATE TABLE IF NOT EXISTS cash_ledger (
#     id INTEGER PRIMARY KEY,
#     external_id INTEGER NOT NULL UNIQUE,
#     portfolio_id INTEGER,
#     timestamp INTEGER NOT NULL,
#     amount NOT NULL,
#     type NOT NULL, -- DEPOSIT / WITHDRAW
#     balance NOT NULL,
#     FOREIGN KEY (portfolio_id) REFERENCES portfolio (id)
#     );

# CREATE TABLE IF NOT EXISTS last_processed_batch (
#     location TEXT PRIMARY KEY,
#     batch NOT NULL UNIQUE
#     );

# CREATE TABLE IF NOT EXISTS end_of_day_position (
#     id INTEGER PRIMARY KEY,
#     portfolio_id INTEGER,
#     stock_id INTEGER,
#     symbol TEXT NOT NULL UNIQUE,
#     date NOT NULL,
#     size NOT NULL,
#     average_price NOT NULL,
#     FOREIGN KEY (portfolio_id) REFERENCES portfolio (id),
#     FOREIGN KEY (stock_id) REFERENCES stock (id)
#     );


from dynaconf import settings
from peewee import DateField, FloatField, ForeignKeyField, IntegerField, Model, SqliteDatabase, TextField

from alfa.log import log
from alfa.util import create_directories_for_path

db = SqliteDatabase(None)


def open_db():
    path = ":memory:"
    if settings.DB_PATH:
        path = settings.DB_PATH
        log.info(f"Initializing database from {path}")
        create_directories_for_path(path)
    db.init(path)
    return db


class BaseModel(Model):
    class Meta:
        database = db


# Stock model
class Stock(BaseModel):
    id = IntegerField(primary_key=True)
    symbol = TextField(unique=True, null=False)
    name = TextField(null=False)

    @staticmethod
    def add_stock(symbol, name):
        """
        Add a new stock to the database.

        :param symbol: The stock symbol (e.g., "AAPL").
        :param name: The stock name (e.g., "Apple Inc.").
        :return: The created Stock object or None if an error occurred.
        """
        try:
            stock = Stock.create(symbol=symbol, name=name)
            log.debug(f"Stock with symbol '{symbol}' was successfully added.")
            return stock
        except Exception as e:
            log.error(f"Error adding {symbol}. {e}")
            return None

    @staticmethod
    def get_stocks():
        """
        Retrieve all stocks from the database.

        :return: A list of Stock objects.
        """
        try:
            stocks = list(Stock.select())
            log.debug(f"Found {len(stocks)} stocks.")
            return stocks
        except Exception as e:  # pragma: no cover
            log.error(f"Error retrieving stocks. {e}")
            return []

    @staticmethod
    def delete_stock(symbol):
        """
        Delete a stock by its symbol.

        :param symbol: The stock symbol to delete (e.g., "AAPL").
        :return: True if deletion was successful, False otherwise.
        """
        try:
            query = Stock.delete().where(Stock.symbol == symbol)
            rows_deleted = query.execute()
            if rows_deleted > 0:
                log.debug(f"Stock with symbol '{symbol}' was successfully deleted.")
                return True
            else:
                log.warning(f"Stock with symbol '{symbol}' not found.")
                return False
        except Exception as e:  # pragma: no cover
            log.error(f"Error deleting stock {symbol}. {e}")
            return False


class Price(BaseModel):
    id = IntegerField(primary_key=True)
    stock_id = ForeignKeyField(Stock, backref="prices", on_delete="CASCADE")
    date = DateField(null=False)
    open = FloatField(null=False)
    high = FloatField(null=False)
    low = FloatField(null=False)
    close = FloatField(null=False)
    adjusted_close = FloatField(null=False)
    volume = IntegerField(null=False)


# Example usage
# if __name__ == "__main__":

#     print(settings.as_dict())

#     db = init_db()
#     db.connect()
#     db.create_tables([Stock, Price])

#     # Add a new stock (if needed)
#     Stock.add_stock("AAPL", "Apple Inc.")
#     Stock.add_stock("MSFT", "Microsoft Corporation")

#     # Retrieve all stocks
#     stocks = Stock.get_stocks()
#     for stock in stocks:
#         print(f"Stock Id: {stock.id}, Symbol: {stock.symbol}, Name: {stock.name}")

#     db.close()
