from pathlib import Path
import pandas as pd
import requests
import lxml
from io import StringIO
import datetime
import yfinance as yf


class GetSources:
    def __init__(self):
        self.path_fundamentus = 'database/fundamentus/'
        self.path_yahoofinance = 'database/yahoo_finance/'
        self.date = datetime.datetime.now().date()

    def get_fundamentus_data(self):
                
        header = {
        'User-Agent': 
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        url = 'https://www.fundamentus.com.br/fii_resultado.php'
        response = requests.get(url,headers=header)

        if response.status_code == 200:
            data = response.text
            df = pd.read_html(StringIO(data), decimal=',', thousands='.')[0]
            df.head()
            # fixing column types
            columns_to_convert = ['FFO Yield','Dividend Yield','Cap Rate','Vacância Média']
            for col in columns_to_convert:
                df[col] = df[col].str.replace('%', '').str.replace('.', '').str.replace(',', '.').astype(float)/100
            
            df.columns = df.columns.str.lower().str.replace(' ','_').str.replace('/','_')

            date = datetime.datetime.now().date()
            df['reference_date'] = date

            df.to_csv(self.path_fundamentus + f'fundamentus_{date}.csv', index=False)

            return df
        else:
            raise Exception(f"Failed to fetch data. Status code: {response.status_code}")
        
    
    def get_yahoofinance_data(self, ticker):
        
        df = yf.download(ticker + '.SA', start='1999-01-01', end=self.date,auto_adjust=False)

        if df.empty:
            return pd.DataFrame()
        else:
            df.reset_index(inplace=True)
            df.columns = [col[0] for col in df.columns]

            df.to_csv(self.path_yahoofinance + f'yfinance_{ticker}.csv', index=False)

            return df

        