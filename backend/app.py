import os
import time
import pytz
import pandas as pd
from io import BytesIO
from historic_data import get_stock_data
from datetime import datetime, timedelta
from all_components import generate_all_data
from realtime_data import generate_realtime_data
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, request, send_file, flash, redirect
from pathlib import Path

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# Timezone for New York (Eastern Time)
eastern = pytz.timezone('America/New_York')

# Define folder structure
# BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# ALL_DATA_DIR = os.path.join(BASE_DIR, 'data', 'all_data')
# REALTIME_DATA_DIR = os.path.join(BASE_DIR, 'data', "realtime_data")

# # Ensure directories exist
# os.makedirs(ALL_DATA_DIR, exist_ok=True)
# os.makedirs(REALTIME_DATA_DIR, exist_ok=True)


# Define the base directory where the "stock-data" folder will be located
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent / 'stock-data'

# Define the full paths for the required folders
SCHEDULED_DATA_DIR = BASE_DIR / 'scheduled-data'
SCHEDULED_DAILY_DIR = SCHEDULED_DATA_DIR / 'daily'
SCHEDULED_REALTIME_DIR = SCHEDULED_DATA_DIR / 'realtime'

MANUAL_DATA_DIR = BASE_DIR / 'manual'
MANUAL_DAILY_DIR = MANUAL_DATA_DIR / 'daily'
MANUAL_REALTIME_DIR = MANUAL_DATA_DIR / 'realtime'
MANUAL_HISTORIC_DIR = MANUAL_DATA_DIR / 'historic'

# Create all the required directories if they don't exist
SCHEDULED_DATA_DIR.mkdir(parents=True, exist_ok=True)
SCHEDULED_DAILY_DIR.mkdir(parents=True, exist_ok=True)
SCHEDULED_REALTIME_DIR.mkdir(parents=True, exist_ok=True)

MANUAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
MANUAL_DAILY_DIR.mkdir(parents=True, exist_ok=True)
MANUAL_REALTIME_DIR.mkdir(parents=True, exist_ok=True)
MANUAL_HISTORIC_DIR.mkdir(parents=True, exist_ok=True)

# Function to generate and save the all data file
def scheduled_download_all_data():
    try:
        print("Running scheduled task: Download All Data")
        output = generate_all_data()
        if output:
            filename = f'scheduled_all_data_{time.strftime("%Y%m%d%H%M%S")}.xlsx'
            file_path = os.path.join(SCHEDULED_DAILY_DIR, filename)
            with open(file_path, 'wb') as f:
                f.write(output.getvalue())
            print(f"All tickers data saved as {filename}")
        else:
            print("Failed to generate all tickers data")
    except Exception as e:
        print(f"Error in scheduled task (Download All Data): {str(e)}")

# Function to generate and save the real-time data file
def scheduled_download_realtime_data():
    try:
        print("Running scheduled task: Download Real-time Data")
        output = generate_realtime_data()
        if output:
            filename = f'scheduled_realtime_data_{time.strftime("%Y%m%d%H%M%S")}.xlsx'
            file_path = os.path.join(SCHEDULED_REALTIME_DIR, filename)
            with open(file_path, 'wb') as f:
                f.write(output.getvalue())
            print(f"Realtime data saved as {filename}")
        else:
            print("Failed to generate real-time data")
    except Exception as e:
        print(f"Error in scheduled task (Download Real-time Data): {str(e)}")

# Set up scheduler
scheduler = BackgroundScheduler()

# Schedule 'download_all_data' at 12 PM EST
scheduler.add_job(scheduled_download_all_data, 'cron', hour=12, minute=0, timezone=eastern)

# Schedule 'download_realtime_data' every hour from 10 AM to 5 PM EST
scheduler.add_job(scheduled_download_realtime_data, 'cron', hour='10-17', minute=0, timezone=eastern)

# Start the scheduler
scheduler.start()

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/download_all_data', methods=['GET', 'POST'])
def download_all_data():
    try:
        index_ticker_map = {}
        # Check if a file was uploaded
        if request.method == 'POST' and 'file' in request.files:
            uploaded_file = request.files['file']
            
            if uploaded_file.filename != '' and uploaded_file.filename.endswith(('.xlsx', '.xls')):
                # Read tickers from uploaded file
                df_tickers = pd.read_excel(uploaded_file)
                if 'Ticker' not in df_tickers.columns or 'Index' not in df_tickers.columns:
                    flash("Excel file must contain 'Ticker' and 'Index' columns")
                    return redirect('/')
                    
                for index, ticker in df_tickers.groupby('Index'):
                    index_ticker_map[index] = ticker['Ticker'].unique().tolist()
                output = generate_all_data(tickers=index_ticker_map)
            else:
                output = generate_all_data()
        else:
            output = generate_all_data()

        if output:
            filename = f'all_tickers_data_{time.strftime("%Y%m%d%H%M%S")}.xlsx'
            file_path = os.path.join(MANUAL_DAILY_DIR, filename)

            # Save the generated data to the file path
            with open(file_path, 'wb') as f:
                f.write(output.getvalue())
        
            # Flash a success message and redirect to the desired page
            flash(f"Data saved successfully.")
            return redirect('/')
        
        flash("Failed to generate all tickers data")
        return redirect('/')
    except Exception as e:
        flash(f"Error generating all tickers data: {str(e)}")
        return redirect('/')
    
@app.route('/download_realtime_data', methods=['GET', 'POST'])
def download_realtime_data():
    try:
        index_ticker_map = {}
        # Check if a file was uploaded
        if request.method == 'POST' and 'file' in request.files:
            uploaded_file = request.files['file']
            
            if uploaded_file.filename != '' and uploaded_file.filename.endswith(('.xlsx', '.xls')):
                # Read tickers from uploaded file
                df_tickers = pd.read_excel(uploaded_file)
                if 'Ticker' not in df_tickers.columns or 'Index' not in df_tickers.columns:
                    flash("Excel file must contain 'Ticker' and 'Index' columns")
                    return redirect('/')
                    
                for index, ticker in df_tickers.groupby('Index'):
                    index_ticker_map[index] = ticker['Ticker'].unique().tolist()
                output = generate_realtime_data(tickers=index_ticker_map)
            else:
                output = generate_realtime_data()
        else:
            output = generate_realtime_data()

        if output:
            filename = f'realtime_data_{time.strftime("%Y%m%d%H%M%S")}.xlsx'
            file_path = os.path.join(MANUAL_REALTIME_DIR, filename)

            # Save the generated data to the file path
            with open(file_path, 'wb') as f:
                f.write(output.getvalue())
        
            # Flash a success message and redirect to the desired page
            flash(f"Realtime data saved successfully.")
            return redirect('/')
        
        flash("Failed to generate realtime data")
        return redirect('/')
    except Exception as e:
        flash(f"Error generating realtime data: {str(e)}")
        return redirect('/')

@app.route('/download', methods=['POST'])
def download():
    try:
        # Get uploaded file
        uploaded_file = request.files['file']
        period_type = request.form['period_type']
        
        # Validate file
        if uploaded_file.filename == '':
            flash('No file selected')
            return redirect('/')

        if not uploaded_file.filename.endswith(('.xlsx', '.xls')):
            flash('Invalid file format. Please upload an Excel file.')
            return redirect('/')

        df_tickers = pd.read_excel(uploaded_file)
        if 'Ticker' not in df_tickers.columns:
            flash("Excel file must contain a 'Ticker' column")
            return redirect('/')

        tickers = df_tickers['Ticker'].unique().tolist()

        # Handle date range or weeks input
        if period_type == 'date':
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            
            # Validate dates
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            if start_date_obj >= end_date_obj:
                flash('End date must be after start date')
                return redirect('/')
        else:
            weeks = int(request.form['weeks'])
            if weeks <= 0:
                flash('Weeks must be a positive number')
                return redirect('/')
            
            end_date_obj = datetime.now()
            start_date_obj = end_date_obj - timedelta(weeks=weeks)
            start_date = start_date_obj.strftime('%Y-%m-%d')
            end_date = end_date_obj.strftime('%Y-%m-%d')

        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for ticker in tickers:
                data = get_stock_data(ticker, start_date, end_date)
                if data is not None and not data.empty:
                    data.to_excel(writer, sheet_name=ticker[:31], index=False)
                else:
                    flash(f"No data found for {ticker} in the given date range")

        output.seek(0)
        filename = f'stock_data_{time.strftime("%Y%m%d%H%M%S")}.xlsx'
        
         # Save the generated file in MANUAL_HISTORIC_DIR
        file_path = os.path.join(MANUAL_HISTORIC_DIR, filename)
        with open(file_path, 'wb') as f:
            f.write(output.getvalue())
        
        # Flash success message and redirect
        flash(f"File has been successfully saved as {filename} in the manual/historic folder.")
        return redirect('/')

    except ValueError as ve:
        flash('Invalid input format. Please check your inputs.')
        return redirect('/')
    except Exception as e:
        flash(f'Error processing request: {str(e)}')
        return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)