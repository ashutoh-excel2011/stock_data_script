import pandas as pd
from io import BytesIO
from google.cloud import storage

SERVICE_ACCOUNT_FILE = 'service2.json'
# Default Template Path
DEFAULT_TEMPLATE = "Development/Scripts/Script-market/Template/default.xlsx"
INDEX_COMPONENTS = "Development/Scripts/Script-market/Template/Index-components/2025-05-04_110036.xlsx"
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
    
def generate_ticker_template(excel_file_path=INDEX_COMPONENTS):
    """
    Creates an Excel template with 'Index' and 'Ticker' columns based on an existing Excel file
    stored in Google Cloud Storage. The structure of the existing Excel should be like the image you gave.
    """

    if not storage_client:
        print("Could not create storage client.")
        return None

    try:
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(excel_file_path)

        file_content = BytesIO()
        blob.download_to_file(file_content)
        file_content.seek(0)

        df = pd.read_excel(file_content)
        # Create empty lists to store Index and Ticker data
        index_list = []
        ticker_list = []

        # Iterate through columns Dow Jones, Nasdaq 100, SP500, ETF, Other
        index_columns = ['SP500', 'DowJones', 'Nasdaq100', 'ETF', 'Other']
        index_names = ['SP500', 'DowJones', 'Nasdaq100', 'ETF', 'Other']

        for i, index_col in enumerate(index_columns):
            if index_col in df.columns:
                # Iterate through rows of the current index column
                for row in df.itertuples():
                    ticker = getattr(row, 'Ticker')
                    if getattr(row, index_col) == 1:
                        index_list.append(index_names[i])  # Append the correct index name
                        ticker_list.append(ticker)

        # Create the new DataFrame for the template
        template_data = {'Index': index_list, 'Ticker': ticker_list}
        template_df = pd.DataFrame(template_data)

        # Create in-memory Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            template_df.to_excel(writer, sheet_name='IndexTickers', index=False)

        # Save to local file
        with open("index_ticker_template.xlsx", 'wb') as f:
            f.write(output.getvalue())
        
        # return True
        output.seek(0)
        return output

    except Exception as e:
        print(f"Error generating index ticker template from Excel file: {e}")
        return None