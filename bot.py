import websocket, json, pprint, talib
import numpy as np
from binance.client import Client
from binance.enums import *
import config
#import actual_config


RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

TRADE_SYMBOL = 'ETHUSD' #Where to find this symbol? TODO
TRADE_QUANTITY = 0.0

# https://github.com/binance/binance-spot-api-docs/blob/master/web-socket-streams.md#general-wss-information
# <streamName> is <symbol>@kline_<interval> (Kline/Candlestick Streams)
SOCKET = "wss://stream.binance.com:9443/ws/ethusdt@kline_1m" 

closes = []
in_position = False #If False buy it, if True sell it
client = Client(config.API_KEY, config.API_SECRET, tld='com')
#client = Client(actual_config.API_KEY, actual_config.API_SECRET, tld='com')

def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET): # ORDER_TYPE_MARKET from binance.enums
    try:
        order = client.create_order( symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
    except Exception as e:
        return False

    return True


def on_open(ws):
    print("Opened Connection")

def on_close(ws):
    print("Closed Connection")

def on_message(ws, message):
    global closes
    json_message = json.loads(message)
    #pprint.pprint(json_message)
    candle = json_message['k']
    close = candle['c']
    if candle['x']:
        print (f"Candle closed at {close}")
        closes.append(float(close))
        print (closes)


        if len(closes) > RSI_PERIOD:
            np_closes = np.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            print(f'RSIs : {rsi}')
            print(f'Current RSI : {rsi[-1]}')

            if rsi[-1] < RSI_OVERSOLD:
                if not in_position: #Added to limit the no. of sell orders to 1. Check 'in_position' logic
                    print ("OVERSOLD...BUY!")
                    #Binance Logic
                    order_success =  order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_success:
                        in_position = True #Now the sell order can be activated
            
            if rsi[-1] > RSI_OVERBOUGHT:
                if in_position:
                    print ("OVERBOUGHT...SELL!")
                    #Binance Logic
                    order_success =  order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_success:
                        in_position = False  # Now the buy order can be activated


ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
ws.run_forever()