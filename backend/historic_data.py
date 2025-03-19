import yfinance as yf
import pandas as pd

def get_stock_data(ticker, start_date, end_date):
    """Fetch stock data for a given ticker and date range"""
    try:
        print(f"Fetching data for {ticker} from {start_date} to {end_date}...")
        
        # Adjust end date using pandas date offset
        end_date_adjusted = pd.to_datetime(end_date) + pd.DateOffset(days=1)
        
        # Fetch data within the given date range
        df = yf.download(ticker, start=start_date, end=end_date_adjusted, group_by='ticker', auto_adjust=False)
        
        if df.empty:
            return None
        
        # Convert index (Datetime) to US/Eastern time and make it naive
        df.index = df.index.tz_localize(None)
        
        # If fetching multiple tickers, yf.download returns a multi-index DataFrame
        if isinstance(df.columns, pd.MultiIndex):
            # Reset index for better structuring
            df = df.stack(level=0, future_stack=True).rename_axis(['Date', 'Ticker']).reset_index()

        # Drop the Volume column
        df = df.drop(columns=['Volume'])

        return df
                
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None