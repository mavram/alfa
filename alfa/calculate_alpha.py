import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import statsmodels.api as sm

def calculate_alpha(risk_free_rate, start_date, end_date):
    # Define portfolio and benchmark
    tickers = ['TSLA', 'IBIT']
    benchmark_ticker = 'SPY'
    shares = [100, 100]
    
    # Download data
    data = yf.download(tickers + [benchmark_ticker], start=start_date, end=end_date)['Adj Close']
    
    # Calculate daily returns
    returns = data.pct_change().dropna()
    
    # Calculate individual betas
    betas = {}
    for ticker in tickers:
        # Run regression of stock returns vs. benchmark returns
        X = returns[benchmark_ticker]
        y = returns[ticker]
        X = sm.add_constant(X)
        model = sm.OLS(y, X).fit()
        betas[ticker] = model.params[benchmark_ticker]
    
    # Calculate portfolio beta as weighted average of individual betas
    total_value = sum([shares[i] * data[ticker].iloc[-1] for i, ticker in enumerate(tickers)])
    weights = [(shares[i] * data[ticker].iloc[-1]) / total_value for i, ticker in enumerate(tickers)]
    portfolio_beta = sum([weights[i] * betas[ticker] for i, ticker in enumerate(tickers)])
    
    # Calculate portfolio return and benchmark return over the period
    portfolio_return = sum([weights[i] * returns[ticker].mean() for i, ticker in enumerate(tickers)]) * len(returns)
    benchmark_return = returns[benchmark_ticker].mean() * len(returns)
    
    # Calculate alpha
    alpha = portfolio_return - (risk_free_rate + portfolio_beta * (benchmark_return - risk_free_rate))
    
    return alpha

# Example usage
risk_free_rate = 0.02  # Annual risk-free rate, e.g., 2%
start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
end_date = datetime.now().strftime('%Y-%m-%d')

alpha = calculate_alpha(risk_free_rate, start_date, end_date)
print(f"Alpha of the portfolio: {alpha:.2%}")
