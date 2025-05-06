import yfinance as yf
import pandas as pd
from io import BytesIO
from utils import get_tickers_from_gcs

def get_current_details(ticker, start_date, end_date):
    """Fetch stock data for a given ticker and date range"""
    try:
        print(f"Fetching data from {start_date} to {end_date}...")
        
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
        else:
            df = df.reset_index()
            df['Ticker'] = ticker

        # Drop the Volume column
        df = df.drop(columns=['Volume'])
        df = df.dropna(subset=['Open', 'High', 'Low', 'Close', 'Adj Close'])
        
        return df
                
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None
    
def generate_historic_data(start_date, end_date, tickers=None, multisheet=None):
    try:
        output = BytesIO()
        all_data = pd.DataFrame()
        
        if tickers:
            # Use provided tickers
            all_tickers = []
            for index, symbols in tickers.items():
                all_tickers.extend([symbol for symbol in symbols if symbol not in all_tickers])
            
            print(f"Processing from {start_date} to {end_date}...")
            df = get_current_details(all_tickers, start_date, end_date)
            if not df.empty:
                all_data = pd.concat([all_data, df], ignore_index=True)
        else:
            # Use default tickers from GCS template
            index_ticker_map = get_tickers_from_gcs()
            if index_ticker_map:
                all_tickers = []
                for index, symbols in index_ticker_map.items():
                    all_tickers.extend([symbol for symbol in symbols if symbol not in all_tickers])

                print(f"Processing from {start_date} to {end_date}...")
                df = get_current_details(all_tickers, start_date, end_date)
                if not df.empty:
                    all_data = pd.concat([all_data, df], ignore_index=True)

            else:
                print("Failed to load tickers from GCS. Aborting data generation.")
                return None # Or whatever error handling you prefer

        # Split datetime into separate date and time columns
        if not all_data.empty:
            all_data['Time'] = pd.to_datetime(all_data['Date']).dt.strftime('%H:%M:%S')
            all_data['Date'] = pd.to_datetime(all_data['Date']).dt.strftime('%Y-%m-%d')

        # Write all data to a single sheet
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            if not all_data.empty:
                cols = ['Ticker', 'Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Adj Close']
                all_data = all_data[cols]
                all_data = all_data.sort_values(['Ticker', 'Date'])
                
                if multisheet:
                    for ticker, group in all_data.groupby('Ticker'):
                        sheet_data = group.drop('Ticker', axis=1)
                        sheet_name = str(ticker)[:31]
                        sheet_data.to_excel(writer, sheet_name=sheet_name, index=False)
                else:
                    all_data.to_excel(writer, sheet_name='Historic Data', index=False)
        output.seek(0)
        return output
    
    except Exception as e:
        print(f"Error generating historic data: {str(e)}")
        return None
