from alfa.portfolio import Portfolio


if __name__ == "__main__":
    portfolio = Portfolio()

    portfolio.buy("TSLA", 100, 150)
    portfolio.buy("TSLA", 100, 170)
    portfolio.sell("TSLA", 50, 180)
    portfolio.sell("TSLA", 300, 180)