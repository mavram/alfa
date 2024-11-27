import os

from dynaconf import settings
from peewee import DateField, FloatField, ForeignKeyField, IntegerField, Model, SqliteDatabase, TextField

from alfa.log import log


def create_directories_for_dbpath(dbpath):
    """
    Create all missing directories in the given path, assuming it ends with a file name.

    :param path: The file path for which directories need to be created.
    """
    try:
        # Extract the directory portion of the path
        directory = os.path.dirname(dbpath)

        # Create directories if they are missing
        if directory:  # Avoid creating root directory if path is just a file name
            os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        log.error(f"Error creating directories: {e}")
        return False


class Database:
    @staticmethod
    def get_database(dbpath):
        if create_directories_for_dbpath(dbpath):
            db = SqliteDatabase(dbpath)
            log.info(f"Database '{dbpath}' was opened.")
            return db
        return None


db = Database.get_database(settings.DB_PATH or f"{settings.PORTFOLIO_NAME}.db")


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
        except Exception as e:
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
        except Exception as e:
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
if __name__ == "__main__":
    db.connect()
    db.create_tables([Stock, Price])

    # Add a new stock (if needed)
    Stock.add_stock("AAPL", "Apple Inc.")
    Stock.add_stock("MSFT", "Microsoft Corporation")

    # Retrieve all stocks
    stocks = Stock.get_stocks()
    for stock in stocks:
        print(f"Stock Id: {stock.id}, Symbol: {stock.symbol}, Name: {stock.name}")

    db.close()
