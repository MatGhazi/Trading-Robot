import time
import hmac
import json
import base64
import urllib
import hashlib
import requests
import sqlite3 as sql
from time import sleep
from yaml import safe_load
from threading import Thread
from concurrent import futures


class UrlParamsBuilder(object):
    def __init__(self):
        self.param_map = dict()
        self.post_map = dict()

    def put_url(self, name, value):
        if value is not None:
            if isinstance(value, list):
                self.param_map[name] = json.dumps(value)
            elif isinstance(value, float):
                self.param_map[name] = ('%.20f' % (value))[
                    slice(0, 16)].rstrip('0').rstrip('.')
            else:
                self.param_map[name] = str(value)

    def put_post(self, name, value):
        if value is not None:
            if isinstance(value, list):
                self.post_map[name] = value
            else:
                self.post_map[name] = str(value)

    def build_url(self):
        if len(self.param_map) == 0:
            return ""
        encoded_param = urllib.parse.urlencode(self.param_map)
        return encoded_param

    def build_url_to_json(self):
        return json.dumps(self.param_map)

def load_yaml(path):
    with open(path) as f:
        return safe_load(f)

def init():
    conf = load_yaml('binance/conf.yml')
    api_key = conf.get('api_key')
    globals()['_API_KEY'] = api_key
    globals()['_API_SECRET'] = conf.get('api_secret')
    # globals()['LEVERAGE'] = conf.get('leverage')
    globals()['TP_FACTOR'] = conf.get('tp_factor')
    globals()['SL_FACTOR'] = conf.get('tp_factor')
    globals()['server_url'] = 'https://fapi.binance.com/'
    globals()['headers'] = {'Content-Type': 'application/json', 'X-MBX-APIKEY': api_key}
    # Thread(target=follow_up).start()

def make_order(**kwargs):
    builder = UrlParamsBuilder()
    builder.put_url("symbol", kwargs.get('symbol'))
    builder.put_url("side", kwargs.get('side'))
    builder.put_url("type", kwargs.get('ordertype'))
    builder.put_url("timeInForce", kwargs.get('timeInForce'))
    builder.put_url("quantity", kwargs.get('quantity'))
    builder.put_url("reduceOnly", kwargs.get('reduceOnly'))
    builder.put_url("price", kwargs.get('price'))
    builder.put_url("newClientOrderId", kwargs.get('newClientOrderId'))
    builder.put_url("stopPrice", kwargs.get('stopPrice'))
    builder.put_url("workingType", kwargs.get('workingType'))
    builder.put_url("closePosition", kwargs.get('closePosition'))
    builder.put_url("positionSide", kwargs.get('positionSide'))
    builder.put_url("callbackRate", kwargs.get('callbackRate'))
    builder.put_url("activationPrice", kwargs.get('activationPrice'))
    builder.put_url("newOrderRespType", kwargs.get('newOrderRespType'))
    builder.put_url("orderId", kwargs.get('binance_id'))
    builder.put_url("startTime", kwargs.get('startTime'))
    builder.put_url("endTime", kwargs.get('endTime'))
    builder.put_url("marginType", kwargs.get('marginType'))
    builder.put_url("leverage", kwargs.get('leverage'))
    builder.put_url("recvWindow", 60000)
    builder.put_url("timestamp", kwargs.get('timestamp'))
    return builder

def signature(secret_key, builder):
    query_string = builder.build_url()
    signature = hmac.new(secret_key.encode(), msg=query_string.encode(
    ), digestmod=hashlib.sha256).hexdigest()
    builder.put_url("signature", signature)

def timestamp():
    return int(round(time.time() * 1000)) - 1000  # diduction in sdk

def set_margin_type(symbol,margin):
    url, method = 'fapi/v1/marginType', 'POST'
    builder = make_order(
        symbol=symbol,
        marginType=margin, # ISOLATED, CROSSED
        timestamp=timestamp(),
    )
    signature(_API_SECRET, builder)
    core_url = server_url + url + "?" + builder.build_url()
    response = requests.request(method, core_url, headers=headers).json()
    if response.get('msg')== 'success' or 'No need to change margin type.':
        return True
    
def set_leverage(symbol,leverage):
    url, method = 'fapi/v1/leverage', 'POST'
    builder = make_order(
        symbol=symbol,
        leverage=leverage,
        timestamp=timestamp(),
    )
    signature(_API_SECRET, builder)
    core_url = server_url + url + "?" + builder.build_url()
    try:
        response = requests.request(method, core_url, headers=headers).json()
        return response.get('leverage') == leverage
    except Exception as e:
        print('>>', e)

def get_price(symbol):
    url, method = 'fapi/v1/ticker/24hr', 'GET'
    builder = make_order(
        symbol=symbol,
        timestamp=timestamp(),
    )
    signature(_API_SECRET, builder)
    core_url = server_url + url + "?" + builder.build_url()
    try:
        response = requests.request(method, core_url, headers=headers).json()
        return response.get('lastPrice')
    except Exception as e:
        print('>>', e)

def check_condetions_n_price(symbol,leverage,margin):
    funcs = [(get_price,[symbol]), (set_margin_type,[symbol,margin]), (set_leverage,[symbol,leverage])]
    r = []
    with futures.ThreadPoolExecutor() as exe:
        for f in funcs:
            r.append(exe.submit(f[0],*f[1]))
        r = [i.result() for i in r]
    if all(r + [r]):
        return r[0]

def round_quantity(amount, symbol, price):
    with open('binance/step.json') as f:
        step = float(json.load(f).get(symbol))
    qty = amount / float(price)
    qty = str((qty // step) * step)
    print(qty)
    return qty

def set_tp_sl(**kwargs):
    url, method = 'fapi/v1/order', 'POST'
    builder = make_order(
        symbol=symbol,
        side='BUY' if positionSide == 'SHORT' else 'SELL',
        positionSide=positionSide,
        ordertype='TAKE_PROFIT_MARKET',
        stopPrice=tp if tp!=None else sl,
        closePosition="true",
        timestamp=timestamp(),
    )
    signature(_API_SECRET, builder)
    core_url = server_url + url + "?" + builder.build_url()
    return requests.request(method, core_url, headers=headers).json()

def trade_history(symbol, startTime='', endTime=''):
    url, method = 'fapi/v1/userTrades', 'GET'
    builder = make_order(
        symbol=symbol,          # optional
        startTime=startTime,    # optional
        endTime=endTime,        # optional
        limit=500,
        timestamp=timestamp(),
    )
    signature(_API_SECRET, builder)
    core_url = server_url + url + "?" + builder.build_url()
    return requests.request(method, core_url, headers=headers).json()

def current_positions(symbol=''):
    url, method = 'fapi/v1/adlQuantile', 'GET'
    builder = make_order(
        symbol=symbol,          #optional
        timestamp=timestamp(),
    )
    signature(_API_SECRET, builder)
    core_url = server_url + url + "?" + builder.build_url()
    return requests.request(method, core_url, headers=headers).json()

def position_information(symbol):
    url, method = 'fapi/v2/positionRisk', 'GET'
    builder = make_order(
        symbol=symbol,          
        timestamp=timestamp(),
    )
    signature(_API_SECRET, builder)
    core_url = server_url + url + "?" + builder.build_url()
    return requests.request(method, core_url, headers=headers).json()

def account_balance():
    url, method = 'fapi/v2/balance', 'GET'
    builder = make_order(
        timestamp=timestamp(),
    )
    signature(_API_SECRET, builder)
    core_url = server_url + url + "?" + builder.build_url()
    return requests.request(method, core_url, headers=headers).json()

def open_orders(symbol=''):
    url, method = 'fapi/v1/openOrders', 'GET'
    builder = make_order(
        symbol=symbol,          #optional
        timestamp=timestamp(),
    )
    signature(_API_SECRET, builder)
    core_url = server_url + url + "?" + builder.build_url()
    return requests.request(method, core_url, headers=headers).json()

def delete_orders(symbol):
    url, method = 'fapi/v1/allOpenOrders', 'DELETE'
    builder = make_order(
        symbol=symbol,  # optional
        timestamp=timestamp(),
    )
    signature(_API_SECRET, builder)
    core_url = server_url + url + "?" + builder.build_url()
    response = requests.request(method, core_url, headers=headers).json()
    print(response)

def open_pos(symbol, amount, positionSide,leverage,margin, tp=None, sl=None):
    url, method = 'fapi/v1/order', 'POST'
    symbol = symbol if symbol.endswith('USDT') else symbol + 'USDT'
    price = check_condetions_n_price(symbol,leverage,margin)
    if not price:
        return 'Something went wrong!'
    if current_positions(symbol):
        return f'There is another open order for {symbol}'
    builder = make_order(
        symbol=symbol,
        side='SELL' if positionSide == 'SHORT' else 'BUY',
        positionSide=positionSide,
        ordertype='MARKET',
        quantity=round_quantity(amount, symbol, price),
        timestamp=timestamp(),
    )
    signature(_API_SECRET, builder)
    core_url = server_url + url + "?" + builder.build_url()
    response = requests.request(method, core_url, headers=headers).json()

    if tp or sl:
        r = []
        kwargs = set_tp_sl.__code__.co_varnames
        with futures.ThreadPoolExecutor() as exe:
            for f in [tp,sl]:
                if f!=None:
                    r.append(exe.submit(set_tp_sl,[symbol,positionSide,tp,sl]))
    return response

    # tp_r, sl_r = {}, {}
    # if response.get('status') == 'NEW':
    #     _tp, _sl = calc_tp_sl(price, positionSide)
    #     tp_r = set_tp(symbol, positionSide, tp or _tp)
    #     sl_r = set_sl(symbol, positionSide, sl or _sl)
    # response = dict(o=response, tp=tp_r, sl=sl_r)
    # for i in response.values():
    #     if i:
    #         i.update(
    #             code=i.get('code', 0),
    #             msg=i.get('msg', ''),
    #             fee=0, pnl=0,
    #         )
    #         store(symbol, i) 
    # return dict(o=response, tp=tp_r, sl=sl_r)

# def position_result(symbol, last=True):
#     symbol = symbol if symbol.endswith('USDT') else symbol + 'USDT'
#     conn = db.connect(symbol)
#     limit = 3 if last else 0
#     data = [i for i in db.read(conn, limit) if i.get('type') == 'MARKET']
#     result = sum([float(i.get('pnl'))-float(i.get('fee')) for i in data])
#     return result

# def follow_up():
#     while True:
#         sleep(30)
#         resultless = dict()
#         for d in db.get_db_list():
#             conn = db.connect(d.split('.')[0])
#             last = [i for i in db.read(conn, 3)]
#             if last:
#                 if last[0].get('status') == 'NEW':
#                     resultless[d.split('.')[0]] = last
#         positions = [i.get('positions') for i in current_positions()]
#         for i in positions:
#             resultless.pop(i, None)
#         for k,v in resultless.items():
#             history = trade_history(k)
#             oids = [i.get('orderId') for i in v]
#             close = [i for i in history if i.get('orderId') in oids]
#             fee = sum([float(i.get('commission')) for i in close])
#             pnl = sum([float(i.get('realizedPnl')) for i in close])
#             oid = [i.get('orderId') for i in v if i.get('type') == 'MARKET'][0]
#             conn = db.connect(k)
#             db.update(conn, dict(orderId=oid), dict(status='done', fee=fee, pnl=pnl))

init()
