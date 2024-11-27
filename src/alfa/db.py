from peewee import DateField, FloatField, ForeignKeyField, IntegerField, Model, SqliteDatabase, TextField

from alfa.log import log


class Database:
    @staticmethod
    def get_database(dbpath):
        return SqliteDatabase(dbpath)


db = Database.get_database("alpha.db")


class BaseModel(Model):
    class Meta:
        database = db


# Stock model
class Stock(BaseModel):
    id = IntegerField(primary_key=True)
    symbol = TextField(unique=True, null=False)
    name = TextField(null=False)

    @staticmethod
    def add_new_stock(symbol, name):
        """
        Add a new stock to the database.

        :param symbol: The stock symbol (e.g., "AAPL").
        :param name: The stock name (e.g., "Apple Inc.").
        :return: The created Stock object or None if an error occurred.
        """
        try:
            return Stock.create(symbol=symbol, name=name)
        except Exception as e:
            log.error(f"Error adding {symbol}. {e}")
            return None

    @staticmethod
    def get_all_stocks():
        """
        Retrieve all stocks from the database.

        :return: A list of Stock objects.
        """
        try:
            return list(Stock.select())
        except Exception as e:
            log.error(f"Error retrieving stocks. {e}")
            return []


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
    Stock.add_new_stock("AAPL", "Apple Inc.")
    Stock.add_new_stock("MSFT", "Microsoft Corporation")

    # Retrieve all stocks
    all_stocks = Stock.get_all_stocks()
    for stock in all_stocks:
        print(f"Stock Id: {stock.id}, Symbol: {stock.symbol}, Name: {stock.name}")

    db.close()
