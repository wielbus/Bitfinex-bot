from dotenv import load_dotenv
import os
import requests
import time
import json
import hashlib
import hmac

load_dotenv()
API_KEY = os.environ.get('BITFINEX_API_KEY')
API_KEY_SECRET = os.environ.get('BITFINEX_API_KEY_SECRET')

BASE_URL = "https://api.bitfinex.com/v2/auth/"

pairs = {
    # 'EURUSD': 'tEURF0:USTF0',
    'XAGUSD': 'tXAGF0:USTF0',
    'XAUUSD': 'tXAUTF0:USTF0',
    'GBPUSD': 'tGBPF0:USTF0',
    'EURUSD': 'tTESTBTCF0:TESTUSDTF0'
}

acceptable_spread = 0.03
# sl_percent = 0.50
collateral = 100
leverage = 50

def nonce():
        return str(int(round(time.time() * 1000)))

def headers(path, nonce, body):
    signature = "/api/v2/auth/" + path + nonce + body
    # print("Signing: " + signature)
    h = hmac.new(API_KEY_SECRET.encode(encoding='UTF-8'),
                    signature.encode(encoding='UTF-8'), hashlib.sha384)
    signature = h.hexdigest()
    return {
        "bfx-nonce": nonce,
        "bfx-apikey": API_KEY,
        "bfx-signature": signature,
        "content-type": "application/json"
    }

# Submit order in API
def Open_position(symbol, direction, amount):
    nonce_ = nonce()
    amount = -amount if direction == 'Sell' else amount
    symbol = pairs[symbol]
    # from checking import leverage
    body = {
        "type": 'MARKET',
        "symbol": f"{symbol}",
        "amount": f"{amount}",
        "lev": f"{leverage}"
    }
    rawBody = json.dumps(body)
    path = "w/order/submit"
    # print(BASE_URL + path)
    # print(nonce_)
    headers_ = headers(path, nonce_, rawBody)
    # print(headers_)
    # print(rawBody)
    # print("requests.post("+BASE_URL + path + ", headers=" + str(headers_) + ", data=" + rawBody + ", verify=True)")
    r = requests.post(BASE_URL + path,
                        headers=headers_, data=rawBody, verify=True)
    print(r.json())
    return r.status_code
     

# def Stop_loss(symbol, amount):
#     nonce_ = nonce()
#     price = 0
#     if amount > 0: # SL must be opposite to opened position, + = LONG, - = SHORT
#         amount = -amount
#         price = Current_price(symbol)*(1-(sl_percent/leverage))
#     else:
#         amount = amount*-1.0
#         price = Current_price(symbol)*((sl_percent/leverage)+1)
#     body = {
#         "type": "STOP",
#         "symbol": f"{symbol}",
#         "price": f"{price}",
#         "amount": f"{amount}",
#         "lev": f"{leverage}",
#         "flags": 1024
#     }
#     print(price)
#     rawBody = json.dumps(body)
#     path = "w/order/submit"
#     headers_ = headers(path, nonce_, rawBody)
#     r = requests.post(BASE_URL + path,
#                         headers=headers_, data=rawBody, verify=True)
#     if r.status_code == 200:
#         print(r.json())

#     else:
#         print(r.json())
#         print(r.status_code)

# def Retrieve_positions():
#     nonce_ = nonce()
#     body = {}
#     rawBody = json.dumps(body)
#     path = "r/positions"
#     headers_ = headers(path, nonce_, rawBody)
#     r = requests.post(BASE_URL + path,
#                         headers=headers_, data=rawBody, verify=True)
#     if r.status_code == 200:
#         x = r.json()
#         print(x)
#         df = pd.DataFrame(columns=['ID','Created','Symbol','Direction','Entry price'])
#         if len(x) == 0:
#             return df

#         for i in x:
#             id = None
#             created = i[12]
#             symbol = list(pairs.keys())[list(pairs.values()).index(i[0])]
#             direction = 'Buy' if i[2]>0 else 'Sell'
#             entry_price = i[3]
#             temp = [id, created, symbol, direction, entry_price]
#             if i[2]/collateral == 1:
#                 df.loc[len(df)] = temp
#             else:
#                 counter = int(i[2]/collateral)
#                 for j in range(counter):
#                     df.loc[len(df)] = temp

#         return df
#     else:
#         print(r.status_code)
#         print(r)
#         return ''

# Submit order in API
def Close_position(symbol, direction, amount):
    nonce_ = nonce()
    amount = -amount if direction == 'Buy' else amount
    symbol = pairs[symbol]
    body = {
        "type": 'MARKET',
        "symbol": f"{symbol}",
        "amount": f"{amount}",
        "flags": 1024 # 512 + 1024 (Close + Reduce Only)
    }
    rawBody = json.dumps(body)
    path = "w/order/submit"
    headers_ = headers(path, nonce_, rawBody)
    r = requests.post(BASE_URL + path,
                        headers=headers_, data=rawBody, verify=True)
    print(r.json())
    return r.status_code


# Derivatives Status History in API
def Spread(symbol):
    url = f"https://api-pub.bitfinex.com/v2/status/deriv?keys={pairs[symbol]}"
    headers_ = {"accept": "application/json"}
    r = requests.get(url, headers=headers_)
    x = list(r.json())
    return ((x[0][3]-x[0][15])/x[0][3])*100.0

# Derivatives Status History in API
def Current_price(symbol):
    url = f"https://api-pub.bitfinex.com/v2/status/deriv?keys={pairs[symbol]}"
    headers_ = {"accept": "application/json"}
    r = requests.get(url, headers=headers_)
    x = list(r.json())
    return x[0][3]

def Platform_status():
    #if returns 1 that means platform is operative
    url = "https://api-pub.bitfinex.com/v2/platform/status"
    headers_ = {"accept": "application/json"}
    r = requests.get(url, headers=headers_)
    return r.json()[0]

# Open_position('tTESTBTCF0:TESTUSDTF0', 'Buy')
# Open_position(999911111, 'Buy', 'tTESTBTCF0:TESTUSDTF0')
# print(Close_position('EURUSD', 'Buy'))