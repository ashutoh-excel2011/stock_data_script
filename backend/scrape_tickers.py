import requests
from bs4 import BeautifulSoup

def get_index_components():
    """Scrape current components of major indices from SlickCharts"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com",
    }

    etf_codes = [
            'SPY', 'SSO', 'SPXL', 'RSP', 'QQQ', 'QLD', 'TQQQ', 'DIA', 'WEBL', 'IWF',
            'XLK', 'XLV', 'XLY', 'XLC', 'XLF', 'XLI', 'XLP', 'XLU', 'XLB', 'XLRE',
            'XLE', 'MDY', 'SPMD', 'SH', 'SDS', 'SPXS', 'PSQ', 'QID', 'SQQQ', 'RWM',
            'GLD', 'SLV', 'USO', 'UNG'
        ]
    
    other_indices = [
        'SPX', 'IXIC', 'DJI', 'N225', 'FTSE', 'FCHI', '^HSI', 'TA35.TA', '^IBEX'
    ]
    
    indices = {
        'SP500': 'https://www.slickcharts.com/sp500',
        'Nasdaq100': 'https://www.slickcharts.com/nasdaq100',
        'DowJones': 'https://www.slickcharts.com/dowjones',
        'ETFs': etf_codes,
        'Other': other_indices
    }

    components = {}
    
    for index, url in indices.items():
        try:
            if index in ['ETFs', 'Other']:
                components[index] = url
                continue
            
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', {'class': 'table table-hover table-borderless table-sm'})

            if not table:
                continue
        
            symbols = []
            rows = table.find('tbody').find_all('tr')

            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 3:
                    continue
                    
                symbol_col = cols[2]
                symbol_link = symbol_col.find('a')
                if not symbol_link:
                    continue
                    
                symbol = symbol_link.text.strip()
                if symbol:
                    symbols.append(symbol)
            
            components[index] = symbols
            
        except Exception as e:
            print(f"Error scraping {index}: {str(e)}")
            
    return components