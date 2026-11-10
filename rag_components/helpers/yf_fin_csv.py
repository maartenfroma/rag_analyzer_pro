import yfinance as yf
from datetime import datetime
import pandas as pd

#THIS RETURNS A DICTIONARY WITH STOCK DATA FOR THE SPECIFIED TICKERS AND
#SAVE CSV 
#SAVE CSV FILE WITH STOCK DATA

stocks=["AAPL", "AMZN"]

for stock in stocks:
    yf.download(stock, start="2026-01-01", end=datetime.now()).to_excel(f"stock_data_{stock}.xlsx")


if __name__ == "__main__":
    print("Stock data for AAPL and AMZN has been saved to Excel files.")      