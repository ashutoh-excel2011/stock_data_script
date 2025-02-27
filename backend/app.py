from flask import Flask, render_template, request, send_file, flash, redirect
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import time
from all_components import generate_all_data
from realtime_data import generate_realtime_data
from historic_data import get_stock_data

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

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
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
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
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
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
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except ValueError as ve:
        flash('Invalid input format. Please check your inputs.')
        return redirect('/')
    except Exception as e:
        flash(f'Error processing request: {str(e)}')
        return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)