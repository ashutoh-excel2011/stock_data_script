import yfinance as yf
import pandas as pd
from io import BytesIO
from scrape_tickers import get_index_components

def get_current_details(tickers):
    """Fetch current market data for a list of tickers"""
    try:
        if not tickers:
            return pd.DataFrame()
            
        data = yf.download(tickers, period="1d", group_by="ticker")
       
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

def generate_all_data(tickers=None):
    """Generate Excel file with all components data in a single sheet"""
    try:
        output = BytesIO()
        all_data = pd.DataFrame()
        
        if tickers:
            # Use provided tickers
            print("Processing custom tickers...")
            df = get_current_details(tickers)
            if not df.empty:
                df['Index'] = 'Custom'
                all_data = df
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
                all_data.to_excel(writer, sheet_name='All Components', index=False)
        
        output.seek(0)
        return output
    
    except Exception as e:
        print(f"Error generating index data: {str(e)}")
        return None
