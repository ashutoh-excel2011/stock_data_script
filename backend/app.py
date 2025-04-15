import os
import time
import tempfile
import pandas as pd
from io import BytesIO
from google.cloud import storage
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from historic_data import generate_historic_data
from datetime import datetime, timedelta
from all_components import generate_all_data
from realtime_data import generate_realtime_data
from specific_date import generate_specific_date_data
from scrape_tickers import generate_index_name
from flask import Flask, render_template, request, flash, redirect

app = Flask(__name__)
app.secret_key = "sp500data1"

# Set up Google Cloud Storage details
GCS_BUCKET_NAME = "sp500data1"

# Define GCS paths based on your structure
GCS_SCHEDULED_DAILY_DIR = "Development/Scripts/Script-market/Stocks-data/Scheduled/Daily/"
GCS_SCHEDULED_REALTIME_DIR = "Development/Scripts/Script-market/Stocks-data/Scheduled/Realtime/"

GCS_MANUAL_DAILY_DIR = "Development/Scripts/Script-market/Stocks-data/Manual/Daily/"
GCS_MANUAL_REALTIME_DIR = "Development/Scripts/Script-market/Stocks-data/Manual/Realtime/"
GCS_MANUAL_HISTORIC_DIR_MULTI = "Development/Scripts/Script-market/Stocks-data/Manual/Historic/Multiple-sheets/"
GCS_MANUAL_HISTORIC_DIR_SINGLE = "Development/Scripts/Script-market/Stocks-data/Manual/Historic/Single-sheet/"
GCS_MANUAL_HISTORIC_DIR_SPECIFIC = "Development/Scripts/Script-market/Stocks-data/Manual/Historic/Specific-date/"
GCS_INDEX_COMPONENTS = "Development/Scripts/Script-market/Template/Index-components"

# Set up Google Drive API credentials
SERVICE_ACCOUNT_FILE = 'g_credentials.json'
SCOPES = ['https://www.googleapis.com/auth/drive']
FOLDER_ID = '1VqWZhF9mcDuB2bib-MDxzOFbcMIJTLbp' 

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)


# Initialize Google Cloud Storage client
storage_client = storage.Client()

# Function to upload a file to Google Drive

def upload_to_drive(file_obj, file_name, folder_path="stocks-data/trash"):
    try:
        folder_names = folder_path.strip('/').split('/')
        parent_id = None

        # Walk through the folder path and create missing folders
        for folder_name in folder_names:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"

            response = drive_service.files().list(q=query, fields="files(id, name)").execute()
            folders = response.get('files', [])

            if folders:
                parent_id = folders[0]['id']
            else:
                metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [parent_id] if parent_id else []
                }
                folder = drive_service.files().create(body=metadata, fields='id').execute()
                parent_id = folder.get('id')

        # Save BytesIO to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            temp_file.write(file_obj.getvalue())
            temp_path = temp_file.name

        # Prepare metadata and upload
        file_metadata = {
            'name': file_name,
            'parents': [parent_id],
        }

        media = MediaFileUpload(temp_path, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        print(f"Uploaded to Google Drive folder")
    except Exception as e:
        print(f"Error uploading: {str(e)}")

    
def upload_to_gcs(file_content, gcs_path):
    """Upload file content (BytesIO) to Google Cloud Storage."""
    try:
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        
        filename = gcs_path.split('/')[-1]
        
        blob = bucket.blob(gcs_path)

        # Upload file content
        blob.upload_from_file(file_content, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        print(f"File uploaded to GCS: gs://{GCS_BUCKET_NAME}/{gcs_path}/{filename}")
    except Exception as e:
        print(f"Error uploading file to GCS: {str(e)}")
        
# Function to generate and save the all data file
@app.route('/run_scheduled_all_data', methods=['POST'])
def scheduled_download_all_data():
    try:
        print("Running scheduled task: Download All Data")
        output = generate_all_data()
        if output:
            filename = f'{time.strftime("%d%m%Y-%H%M%S")}.xlsx'
            drive_filename = f'stocksdata-scheduled-daily-{filename}'
            gcs_path = GCS_SCHEDULED_DAILY_DIR + filename

            # Upload in Google Drive
            upload_to_drive(output, drive_filename, folder_path="stocks-data/scheduled/daily")
            
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
            filename = f'{time.strftime("%d%m%Y-%H%M%S")}.xlsx'
            drive_filename = f'stocksdata-scheduled-realtime-{filename}'
            gcs_path = GCS_SCHEDULED_REALTIME_DIR + filename

            # Upload in Google Drive
            upload_to_drive(output, drive_filename, folder_path="stocks-data/scheduled/realtime")
            
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
            filename = f'{time.strftime("%d%m%Y-%H%M%S")}-dates-{time.strftime("%d%m%Y")}.xlsx'
            drive_filename = f'stocksdata-manual-daily-{filename}'
            gcs_path = GCS_MANUAL_DAILY_DIR + filename

            # Upload in Google Drive
            upload_to_drive(output, drive_filename, folder_path="stocks-data/manual/daily")
            
            # Upload to GCS
            upload_to_gcs(output, gcs_path)
        
            flash(f"File saved successfully.")
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
            filename = f'{time.strftime("%d%m%Y-%H%M%S")}-dates-{time.strftime("%d%m%Y")}.xlsx'
            drive_filename = f'stocksdata-manual-realtime-{filename}'
            gcs_path = GCS_MANUAL_REALTIME_DIR + filename
            
            # Upload in Google Drive
            upload_to_drive(output, drive_filename, folder_path="stocks-data/manual/realtime")
            
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
                filename = f'{time.strftime("%d%m%Y-%H%M%S")}-dates-{specific_date}.xlsx'
                drive_filename = f'stocksdata-manual-historic-specific-date-{filename}'
                gcs_path = GCS_MANUAL_HISTORIC_DIR_SPECIFIC + filename

                # Upload in Google Drive
                upload_to_drive(output, drive_filename, folder_path="stocks-data/manual/historic/specific-date")
            
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
        index_ticker_map = {}
        period_type = request.form['period_type']
        export_format = request.form['export_format']
        
        if 'file' in request.files:
            uploaded_file = request.files['file']
            
            if uploaded_file and uploaded_file.filename.endswith(('.xlsx', '.xls')):
                df_tickers = pd.read_excel(uploaded_file)
                if 'Ticker' not in df_tickers.columns or 'Index' not in df_tickers.columns:
                    flash("Excel file must contain 'Ticker' and 'Index' columns")
                    return redirect('/')
                
                for index, ticker in df_tickers.groupby('Index'):
                    index_ticker_map[index] = ticker['Ticker'].unique().tolist()
            elif uploaded_file.filename != '':
                flash('Invalid file format. Please upload an Excel file.')
                return redirect('/')

         # Handle date range, weeks, or days input
        if period_type == 'date':
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            
            # Validate dates
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            if start_date_obj >= end_date_obj:
                flash('End date must be after start date')
                return redirect('/')
        elif period_type == 'weeks':
            weeks = int(request.form['weeks'])
            if weeks <= 0:
                flash('Weeks must be a positive number')
                return redirect('/')
            
            end_date_obj = datetime.now()
            start_date_obj = end_date_obj - timedelta(weeks=weeks)
            start_date = start_date_obj.strftime('%Y-%m-%d')
            end_date = end_date_obj.strftime('%Y-%m-%d')
        else:  # period_type == 'days'
            days = int(request.form['days'])
            if days <= 0:
                flash('Days must be a positive number')
                return redirect('/')
            
            end_date_obj = datetime.now()
            start_date_obj = end_date_obj - timedelta(days=days)
            start_date = start_date_obj.strftime('%Y-%m-%d')
            end_date = end_date_obj.strftime('%Y-%m-%d')


        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            if index_ticker_map:
                if export_format == 'single':
                    sheet_type = 'singlesheet'
                    
                    output = generate_historic_data(start_date, end_date, tickers=index_ticker_map)
                else:
                    # Multiple sheets - one per ticker
                    sheet_type = 'multisheet'
                    output = generate_historic_data(start_date, end_date, tickers=index_ticker_map, multisheet=True)
            else:
                if export_format == 'single':
                    sheet_type = 'singlesheet'
                    output = generate_historic_data(start_date, end_date)
                else:
                    sheet_type = 'multisheet'
                    output = generate_historic_data(start_date, end_date, tickers=None, multisheet=True)                 

        output.seek(0)
        filename = f'{time.strftime("%d%m%Y-%H%M%S")}-dates-{start_date.replace("-", "")}-{end_date.replace("-", "")}.xlsx'
        drive_filename = f'stocksdata-manual-historic-{sheet_type}-{filename}'
        
        # Set GCS path based on export format
        if export_format == 'single':
            gcs_path = GCS_MANUAL_HISTORIC_DIR_SINGLE + filename
        else:
            gcs_path = GCS_MANUAL_HISTORIC_DIR_MULTI + filename
        
        # Upload in Google Drive
        upload_to_drive(output, drive_filename, folder_path="stocks-data/manual/historic/single-sheet" if export_format == 'single' else "stocks-data/manual/historic/multiple-sheets")
    
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

@app.route('/download-index-components', methods=['POST'])
def download_index_components():
    try:
        output = generate_index_name()
        filename = f'{time.strftime("%Y-%m-%d_%H%M%S")}.xlsx'
        drive_filename = f'index-components-{filename}'
        gcs_path = GCS_INDEX_COMPONENTS + filename
        
        upload_to_gcs(output, gcs_path)
        
        upload_to_drive(output, drive_filename, folder_path="stocks-data/index-components")
        
        flash("Index components data saved successfully.")
        return redirect('/')
    except Exception as e:
        flash(f"Error saving index components data: {str(e)}")
        return redirect('/')

if __name__ == '__main__':
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)