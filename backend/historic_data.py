import yfinance as yf
import pandas as pd
from io import BytesIO
from scrape_tickers import get_index_components

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

        # Drop the Volume column
        df = df.drop(columns=['Volume'])

        return df
                
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None
    
def generate_historic_data(start_date, end_date, tickers=None, multisheet=None):
    """Generate Excel file with specific date data in a single sheet"""
    try:
        output = BytesIO()
        all_data = pd.DataFrame()
        
        if tickers:
            # Use provided tickers
            for index, symbols in tickers.items():
                print(f"Processing {index} for {start_date} to {end_date}...")
                df = get_current_details(symbols, start_date, end_date)
                if not df.empty:
                    df['Index'] = index
                    all_data = pd.concat([all_data, df], ignore_index=True)
        else:
            # Use default index components
            components, _ = get_index_components()
            for index, symbols in components.items():
                print(f"Processing {index} for {start_date} to {end_date}...")
                df = get_current_details(symbols, start_date, end_date)
                if not df.empty:
                    df['Index'] = index
                    all_data = pd.concat([all_data, df], ignore_index=True)

        # Write all data to a single sheet
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            if not all_data.empty:
                cols = ['Ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Adj Close']
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
        print(f"Error generating specific date data: {str(e)}")
        return None
