import pandas as pd
from io import BytesIO
from google.cloud import storage

SERVICE_ACCOUNT_FILE = 'service2.json'
# Default Template Path
DEFAULT_TEMPLATE = "Development/Scripts/Script-market/Template/default.xlsx"
GCS_BUCKET_NAME = "sp500data1"

# Function to create a Google Cloud Storage client
def create_storage_client():
    try:
        # storage_client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_FILE)
        storage_client = storage.Client()
        
        return storage_client

    except Exception as e:
        print(f"Error creating storage client: {e}")
        return None

storage_client = create_storage_client()

# Function to get tickers from GCS bucket
def get_tickers_from_gcs():
    """Downloads ticker data from a GCS bucket, using DEFAULT_TEMPLATE filepath"""
    try:
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(DEFAULT_TEMPLATE)

        file_content = BytesIO()
        blob.download_to_file(file_content)
        file_content.seek(0)

        df = pd.read_excel(file_content)

        if 'Ticker' not in df.columns or 'Index' not in df.columns:
            print("Error: Excel file must contain 'Ticker' and 'Index' columns.")
            return None

        index_ticker_map = {}
        for index, ticker in df.groupby('Index'):
            index_ticker_map[index] = ticker['Ticker'].unique().tolist()

        return index_ticker_map

    except Exception as e:
        print(f"Error reading tickers from GCS: {e}")
        return None