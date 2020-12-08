import pandas as pd 
from datetime import datetime
import cloudscraper

url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=500"

param = {
    'symbol':'BTCUSDT',
    'interval':'15m',
    'limit':500
    }
# scraper = cloudscraper.create_scraper()
# response = cloudscraper.get(url,params=param)


with open('ohlc.txt','r') as response:
    response = response.read()

def framing(response):
    tot = eval(response)
    # print(type(data))
    df = pd.DataFrame(columns=['date'])
    for data in tot:
        ts = int(data[0])
        date = datetime.utcfromtimestamp(ts/1000).strftime('%Y-%m-%d %H:%M:%S')
        row = {
            'date' : date,
            'open' : data[1],
            'low'  : data[2],
            'high' : data[3],
            'open' : data[4],
            'volume' : data[9]
            }
        # print(row.get('high'))
        df=df.append(row,ignore_index=True)
    return df

df = framing(response)
print(df.head())















