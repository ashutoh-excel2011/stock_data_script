import yfinance as yf
import pandas as pd
from io import BytesIO
from scrape_tickers import get_index_components

def get_current_details(tickers):
    """Fetch current market data for a list of tickers"""
    try:
        if not tickers:
            return pd.DataFrame()
            
        data = yf.download(tickers, period="1d", interval="1m", group_by="ticker")
       
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

        return data[data['Date'] == data['Date'].max()]

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
            # Use default index components
            components = get_index_components()
            for index, symbols in components.items():
                print(f"Processing {index}...")
                df = get_current_details(symbols)
                if not df.empty:
                    df['Index'] = index
                    all_data = pd.concat([all_data, df], ignore_index=True)
        
        # Write all data to a single sheet
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            if not all_data.empty:
                cols = ['Index', 'Ticker', 'Date', 'Open', 'High', 'Low', 'Close']
                all_data = all_data[cols]
                all_data.to_excel(writer, sheet_name='Realtime Data', index=False)
        
        output.seek(0)
        return output
    
    except Exception as e:
        print(f"Error generating realtime data: {str(e)}")
        return None