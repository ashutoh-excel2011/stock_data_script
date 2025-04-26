import yfinance as yf
import pandas as pd
from io import BytesIO
from utils import get_tickers_from_gcs

def get_current_details(tickers):
    """Fetch current market data for a list of tickers"""
    try:
        if not tickers:
            return pd.DataFrame()
            
        data = yf.download(tickers, period="1d", interval="1m", group_by="ticker", auto_adjust=False, ignore_tz=True)
       
        if data.empty:
            return pd.DataFrame()

        data.index = data.index.tz_localize(None)
        
        if isinstance(data.columns, pd.MultiIndex):
            data = (data.stack(level=0, future_stack=True)
                    .rename_axis(['Date', 'Ticker'])
                    .reset_index()
                    .drop(columns=['Volume']))
        else:
            data = data.reset_index()
            data['Ticker'] = tickers[0]
            data = data.drop(columns=['Volume'])

        latest_data = data[data['Date'] == data['Date'].max()]
        
        # **Sort the DataFrame by Ticker**
        latest_data = latest_data.sort_values(by=['Ticker']).reset_index(drop=True)
        
        return latest_data

    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

def generate_realtime_data(tickers=None):
    """Generate Excel file with realtime data in a single sheet"""
    try:
        output = BytesIO()
        all_data = pd.DataFrame()
        
        if tickers:
            # Use provided tickers
            for index, symbols in tickers.items():
                print(f"Processing {index}...")
                df = get_current_details(symbols)
                if not df.empty:
                    df['Index'] = index
                    all_data = pd.concat([all_data, df], ignore_index=True)
        else:
            # Use default tickers from GCS template
            index_ticker_map = get_tickers_from_gcs()
            if index_ticker_map:
                for index, symbols in index_ticker_map.items():
                    print(f"Processing {index}...")
                    df = get_current_details(symbols)
                    if not df.empty:
                        df['Index'] = index
                        all_data = pd.concat([all_data, df], ignore_index=True)
            else:
                print("Failed to load tickers from GCS. Aborting data generation.")
                return None
        
        
        # Split datetime into separate date and time columns
        if not all_data.empty:
            all_data['Time'] = pd.to_datetime(all_data['Date']).dt.strftime('%H:%M:%S')
            all_data['Date'] = pd.to_datetime(all_data['Date']).dt.strftime('%Y-%m-%d')
            
        # Write all data to a single sheet
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            if not all_data.empty:
                cols = ['Ticker', 'Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Adj Close']
                all_data = all_data[cols]
                all_data.to_excel(writer, sheet_name='Realtime Data', index=False)
        
        output.seek(0)
        return output
    
    except Exception as e:
        print(f"Error generating realtime data: {str(e)}")
        return None
