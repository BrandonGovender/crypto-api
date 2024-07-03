import websockets
import asyncio
import OrderBook
import json
import sys

from heapq import nsmallest
from typing import List
from fastapi import FastAPI
from contextlib import asynccontextmanager

orderBook = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    global orderBook
    asyncio.create_task(subscribe_to_order_book())
    yield

app = FastAPI(lifespan=lifespan)

async def subscribe_to_order_book():
    global orderBook
    url = "wss://api.valr.com/ws/trade"    
    
    async with websockets.connect(url) as websocket:
        print("Connection opened")
        auth_data = {
            "type": "SUBSCRIBE",
            "subscriptions": [
                {
                    "event": "FULL_ORDERBOOK_UPDATE",
                    "pairs": [
                        "USDTZAR"
                    ]
                }
            ]
        }
        subscribe_message = json.dumps(auth_data)
        await websocket.send(subscribe_message)

        flagger: bool = True #triggers initial orderbook fetch then switches to update protocol
        match_found: bool = False #monitors if uuid is matched in orderbook stored in memory

        try:
            while True:
                message = await websocket.recv()
                message = json.loads(message)

                try:
                    if flagger:
                        orderBook = OrderBook.OrderBook(message)
                        flagger = False
                    else:
                        new_orderBook = OrderBook.OrderBook(message)

                        #For Asks to be updated
                        asks: List[OrderBook.Ask] = orderBook.data['Asks']
                        updated_asks: List[OrderBook.Ask] = new_orderBook.data['Asks']

                        for i in range(len(updated_asks)):
                            orders_a_updated: List[OrderBook.Order] = updated_asks[i]['Orders']
                            if len(orders_a_updated) > 0:
                                for x in range(len(orders_a_updated)):
                                    match_found = False

                                    for y in range(len(asks)):
                                        orders_a: List[OrderBook.Order] = asks[y]['Orders']
                                        for z in range(len(orders_a)):
                                            if orders_a_updated[x]['orderId'] == orders_a[z]['orderId']:
                                                asks[y]['Price'] = updated_asks[i]['Price']
                                                orders_a[z]['quantity'] = updated_asks[x]['quantity']
                                                match_found = True

                                    # f.write(f"record asks    {orders_a_updated[i]['Price']} {orders_a_updated[x]}\n\n\n") 
                                    if not match_found:
                                        record_a: OrderBook.Ask = []
                                        record_a.price = orders_a_updated[i]['Price']
                                        rec_order_a: OrderBook.OrderBook = orders_a_updated[x]
                                        record_a.orders.append(rec_order_a)
                                        orderBook.data.asks.append(record_a)

                        #For Bids to be updated
                        bids: List[OrderBook.Ask] = orderBook.data['Bids']
                        updated_bids: List[OrderBook.Ask] = new_orderBook.data['Bids']

                        for i in range(len(updated_bids)):
                            orders_b_updated: List[OrderBook.Order] = updated_bids[i]['Orders']
                            if len(orders_b_updated) > 0:
                                for x in range(len(orders_b_updated)):
                                    match_found = False

                                    for y in range(len(bids)):
                                        orders_b: List[OrderBook.Order] = bids[y]['Orders']
                                        for z in range(len(orders_b)):
                                            if orders_b_updated[x]['orderId'] == orders_b[z]['orderId']:
                                                bids[y]['Price'] = updated_bids[i]['Price']
                                                orders_b[z]['quantity'] = updated_bids[x]['quantity']
                                                match_found = True

                                    if not match_found:
                                        record_b: OrderBook.Ask = []
                                        record_b.price = orders_b_updated[i]['Price']
                                        rec_order_b: OrderBook.OrderBook = orders_b_updated[x]
                                        record_b.orders.append(rec_order_b)
                                        orderBook.data.bids.append(record_b)                     
                        
                except:                 
                    continue

        except websockets.ConnectionClosed:
            print("Connection closed")
 
# def get_closest_quantity(number, top):
#     orderBook
#     differences = [(abs(num - target), num) for num in numbers]
#     return nsmallest(5, differences, key=lambda x: x[0])

# api_key_secret = ''
# api_key = ''

# def sign_request(api_key_secret, timestamp, verb, path, body = ""):
#     payload = "{}{}{}{}".format(timestamp,verb.upper(),path,body)
#     message = bytearray(payload,'utf-8')
#     signature = hmac.new( bytearray(api_key_secret,'utf-8'), message, digestmod=hashlib.sha512).hexdigest()
#     return signature

# def orderBook():
#     timestamp = str(int(time.time()*1000))
#     verb = "GET"
#     path = "/v1/public/BTCUSDC/orderbook/full"
#     signature = sign_request(api_key_secret, timestamp, verb, path)

#     url = "https://api.valr.com/v1/public/BTCUSDC/orderbook/full"

#     headers = {
#         'Content-Type': 'application/json',
#         'X-VALR-API-KEY': api_key,
#         'X-VALR-SIGNATURE': signature,
#         'X-VALR-TIMESTAMP': timestamp,
#     }

#     try:
#         response = requests.request("GET", url, headers=headers)
        
#         if response.status_code == 200:
#             data = response.json()
#             return data
#         else:
#             print(f"Failed to retrieve data. Status code: {response.status_code}")
#             return None
    
#     except requests.exceptions.RequestException as e:
#         print(f"An error occurred: {e}")
#         return None
    
# @app.get("/api")
# async def orderBook_Test():
#     return orderBook()

@app.get("/api")
async def BestPriceZar(USDT):
    push_float: float = 0
    try:    
        push_float = float(USDT)
    except:
        return 0   
    if push_float == 0:
        return 0

    orderBook = await getOrderBook()
    bids: List[OrderBook.Ask] = orderBook.data['Bids']

    miniBooks: List[OrderBook.MiniBook] = []
    mini: OrderBook.MiniBook = []

    for i in range(len(bids)):
        orders: List[OrderBook.Order] = bids[i]['Orders']
        for y in range(len(orders)):
            mini = OrderBook.MiniBook(price = float(bids[i]['Price']), quantity = float(orders[y]['quantity']))
            miniBooks.append(mini)

    miniBooks = sorted(miniBooks, key=lambda x: x.quantity, reverse=True)

    differences = [(abs(x.quantity - push_float), x) for x in miniBooks]
    
    top_5 = nsmallest(5, differences, key=lambda x: x[0])
    best_zar: float = sys.float_info.max
    top_5_listed: List[float] = []

    perfectFit: bool = False
    for diff, i in top_5:
        top_5_listed.append(i.price)
        if(diff == 0 and i.price < best_zar):
            perfectFit = True
            best_zar = i.price

    if not perfectFit:
        best_zar = min(top_5_listed[0], top_5_listed[1], top_5_listed[2])

    return best_zar

async def getOrderBook():
    return orderBook