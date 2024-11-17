from alfa.portfolio import Portfolio

if __name__ == "__main__":
    portfolio = Portfolio()

    portfolio.deposit(16000)
    portfolio.buy("TSLA", 100, 150)
    portfolio.buy("TSLA", 100, 170)
    portfolio.sell("TSLA", 50, 180)
    print(f"cash balance: {portfolio.get_cash()}")
    portfolio.buy("TSLA", 300, 180)
