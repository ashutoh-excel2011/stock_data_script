import os
import time
import pandas as pd
from io import BytesIO
from google.cloud import storage
from historic_data import get_stock_data
from datetime import datetime, timedelta
from all_components import generate_all_data
from realtime_data import generate_realtime_data
from specific_date import generate_specific_date_data
from flask import Flask, render_template, request, flash, redirect

app = Flask(__name__)
app.secret_key = "sp500data1"

# Set up Google Cloud Storage details
GCS_BUCKET_NAME = "sp500data1"

# Define GCS paths based on your structure
GCS_SCHEDULED_DAILY_DIR = "Scripts/Script-market/Stocks-data/Scheduled/Daily/"
GCS_SCHEDULED_REALTIME_DIR = "Scripts/Script-market/Stocks-data/Scheduled/Realtime/"

GCS_MANUAL_DAILY_DIR = "Scripts/Script-market/Stocks-data/Manual/Daily/"
GCS_MANUAL_REALTIME_DIR = "Scripts/Script-market/Stocks-data/Manual/Realtime/"
GCS_MANUAL_HISTORIC_DIR = "Scripts/Script-market/Stocks-data/Manual/Historic/"

# Initialize Google Cloud Storage client
storage_client = storage.Client()

def upload_to_gcs(file_content, gcs_path):
    """Upload file content (BytesIO) to Google Cloud Storage."""
    try:
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(gcs_path)

        # Upload file content
        blob.upload_from_file(file_content, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        print(f"File uploaded to GCS: gs://{GCS_BUCKET_NAME}/{gcs_path}")
    except Exception as e:
        print(f"Error uploading file to GCS: {str(e)}")
        
# Function to generate and save the all data file
@app.route('/run_scheduled_all_data', methods=['POST'])
def scheduled_download_all_data():
    try:
        print("Running scheduled task: Download All Data")
        output = generate_all_data()
        if output:
            filename = f'scheduled_all_data_{time.strftime("%Y-%m-%d_%H%M%S")}.xlsx'
            gcs_path = GCS_SCHEDULED_DAILY_DIR + filename

            # Upload to GCS
            upload_to_gcs(output, gcs_path)
            
            print(f"All tickers data saved as {filename}")
        else:
            print("Failed to generate all tickers data")
    except Exception as e:
        print(f"Error in scheduled task (Download All Data): {str(e)}")

# Function to generate and save the real-time data file
@app.route('/run_scheduled_realtime_data', methods=['POST'])
def scheduled_download_realtime_data():
    try:
        print("Running scheduled task: Download Real-time Data")
        output = generate_realtime_data()
        if output:
            filename = f'scheduled_realtime_data_{time.strftime("%Y-%m-%d_%H%M%S")}.xlsx'
            gcs_path = GCS_SCHEDULED_REALTIME_DIR + filename

            # Upload to GCS
            upload_to_gcs(output, gcs_path)
            
            print(f"Realtime data saved as {filename}")
        else:
            print("Failed to generate real-time data")
    except Exception as e:
        print(f"Error in scheduled task (Download Real-time Data): {str(e)}")

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
            filename = f'all_tickers_data_{time.strftime("%Y-%m-%d_%H%M%S")}.xlsx'
            gcs_path = GCS_MANUAL_DAILY_DIR + filename

            # Upload to GCS
            upload_to_gcs(output, gcs_path)
        
            flash(f"Data saved successfully to GCS.")
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
            filename = f'realtime_data_{time.strftime("%Y-%m-%d_%H%M%S")}.xlsx'
            # file_path = os.path.join(MANUAL_REALTIME_DIR, filename)
            gcs_path = GCS_MANUAL_REALTIME_DIR + filename

            # Upload to GCS
            upload_to_gcs(output, gcs_path)
        
            # Flash a success message and redirect to the desired page
            flash(f"Realtime data saved successfully.")
            return redirect('/')
        
        flash("Failed to generate realtime data")
        return redirect('/')
    except Exception as e:
        flash(f"Error generating realtime data: {str(e)}")
        return redirect('/')
    
@app.route('/download_specific_date', methods=['GET', 'POST'])
def download_specific_date():
    try:
        index_ticker_map = {}
        # Check if it's a POST request
        if request.method == 'POST' and 'specific_date' in request.form:
            
            specific_date = request.form['specific_date']

            # Check if file was uploaded
            if 'file' in request.files:
                uploaded_file = request.files['file']
                if uploaded_file.filename != '' and uploaded_file.filename.endswith(('.xlsx', '.xls')):
                    # Read tickers from uploaded file
                    df_tickers = pd.read_excel(uploaded_file)
                    if 'Ticker' not in df_tickers.columns or 'Index' not in df_tickers.columns:
                        flash("Excel file must contain 'Ticker' and 'Index' columns")
                        return redirect('/')
                        
                    for index, ticker in df_tickers.groupby('Index'):
                        index_ticker_map[index] = ticker['Ticker'].unique().tolist()
                    
                    output = generate_specific_date_data(specific_date, tickers=index_ticker_map)
                else:
                    output = generate_specific_date_data(specific_date)
            else:
                output = generate_specific_date_data(specific_date)

            if output:
                # Generate filename and save file
                filename = f'specific_date_data_{specific_date}_{time.strftime("%H%M%S")}.xlsx'
                # file_path = os.path.join(MANUAL_HISTORIC_DIR, filename)
                gcs_path = GCS_MANUAL_HISTORIC_DIR + filename

                # Upload to GCS
                upload_to_gcs(output, gcs_path)
                
                
                flash("Data saved successfully.")
                return redirect('/')
            else:
                flash("Failed to generate data for the specific date")
                return redirect('/')
        else:
            flash("Please submit the form with a valid date")
            return redirect('/')
            
    except Exception as e:
        flash(f"Error processing request: {str(e)}")
        return redirect('/')

@app.route('/download', methods=['POST'])
def download():
    try:
        # Get uploaded file
        uploaded_file = request.files['file']
        period_type = request.form['period_type']
        export_format = request.form['export_format']
        
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
            if export_format == 'single':
                # Combine all data into a single sheet
                all_data = []
                for ticker in tickers:
                    data = get_stock_data(ticker, start_date, end_date)
                    if data is not None and not data.empty:
                        data['Ticker'] = ticker  # Add ticker column
                        all_data.append(data)
                    else:
                        flash(f"No data found for {ticker} in the given date range")
                
                if all_data:
                    combined_data = pd.concat(all_data, ignore_index=True)
                    combined_data.to_excel(writer, sheet_name='Historic Data', index=False)
            else:
                # Multiple sheets - one per ticker
                for ticker in tickers:
                    data = get_stock_data(ticker, start_date, end_date)
                    if data is not None and not data.empty:
                        data.to_excel(writer, sheet_name=ticker[:31], index=False)
                    else:
                        flash(f"No data found for {ticker} in the given date range")

        output.seek(0)
        filename = f'stock_data_{time.strftime("%Y-%m-%d_%H%M%S")}.xlsx'
        
        gcs_path = GCS_MANUAL_HISTORIC_DIR + filename

        # Upload to GCS
        upload_to_gcs(output, gcs_path)
        
        # Flash success message and redirect
        flash(f"File successfully saved.")
        return redirect('/')

    except ValueError as ve:
        flash('Invalid input format. Please check your inputs.')
        return redirect('/')
    except Exception as e:
        flash(f'Error processing request: {str(e)}')
        return redirect('/')

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)