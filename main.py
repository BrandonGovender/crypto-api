import websockets
import asyncio
import OrderBook
import json
import sys

from heapq import nsmallest
from typing import List
from fastapi import FastAPI
from contextlib import asynccontextmanager
import requests

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

#get zar
@app.get("/api/get_zar")
async def Get_Best_Price_In_Zar(USDT):
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

#get_coin_list
@app.get("/api/get_coin_list")
async def Get_Meme_Coin_List(): 
    Coins: List[OrderBook.Ticker] = []
    tick: OrderBook.Ticker = []
    memes: List[str] = ["DOGE", "SHIB", "PEPE", "WIF"]

    for meme_coin in memes:
        tick = await getMemeCoin(meme_coin)
        Coins.append(tick)

    return Coins

async def getMemeCoin(name):
    url = "https://api.binance.com/api/v3/depth?symbol="+name+"USDT&limit=1"
    try:
        response = requests.request("GET", url)
        
        if response.status_code == 200:
            message = response.json()
            MemeCoin = OrderBook.OrderBook_MemeCoin(message)
            return await MemeCoinToTicker(name, MemeCoin)

        else:
            print(f"Failed to retrieve data. Status code: {response.status_code}")
            return None
    
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

async def MemeCoinToTicker(name: str, MemeCoin: OrderBook.OrderBook_MemeCoin):
    ticker: OrderBook.Ticker = []
    bids = MemeCoin.bids[0]
    prize_zar = await Get_Best_Price_In_Zar(bids[1])
    ticker = OrderBook.Ticker(symbol = name, mcap = bids[1], price = prize_zar)
    return ticker

# default_ticker: List[OrderBook.Ticker] = [
#         OrderBook.Ticker(symbol="BTC", mcap=20000, price=50),
#         OrderBook.Ticker(symbol="ETH", mcap=10000, price=25),
#         OrderBook.Ticker(symbol="LTC", mcap=5000, price=10)
# ]

#Balance index. Gets MemeCoins and converts to Zar prices when tickers is empty or none
@app.post("/api/balance_index")
async def Balanced_Index(asset_cap: float, total_capital: float, tickers: List[OrderBook.Ticker] = []):
    if(not tickers or tickers == [] or tickers == None or len(tickers) == 0 ):
        tickers = await Get_Meme_Coin_List()
    BalancedOutput: List[OrderBook.BalancedOutput] = []
    Alloted_percent: List[float] = []
    no_balance: bool = False
    min_cap: float = 0

    grand_allot: float = 0
    for coin in tickers:
        grand_allot += coin.mcap
    for coin in tickers:
        Alloted_percent.append((coin.mcap/grand_allot)*100) #calcs ratio to spend all captial based on total max mcap of index

    #sanity checks
    if (asset_cap <= 0 or asset_cap >= 1):
        no_balance = True
    min_cap = 1/len(tickers)
    
    if asset_cap < min_cap:
        for i in range(len(Alloted_percent)):
            Alloted_percent[i] = min_cap*100
        no_balance = True

    if not no_balance:
        Alloted_percent = recursive_rebalancing(Alloted_percent, asset_cap*100)

    for i in range(len(Alloted_percent)):
        value: float = total_capital*(Alloted_percent[i]/100)
        BalancedOutput.append(OrderBook.BalancedOutput( 
            symbol= tickers[i].symbol, 
            amount= round((value/tickers[i].price), 6), 
            zar_value= round(value, 2), 
            percent= round(Alloted_percent[i], 4) ))

    return BalancedOutput

def recursive_rebalancing(Alloted_percent: List[float], asset_cap: float):
    residue_percent: float = 0
    insert_index: int = 0
    balanced_percent: float = 0
    recursive: bool = False

    for i in range(len(Alloted_percent)):
        if Alloted_percent[i] > (asset_cap):
            residue_percent = Alloted_percent[i] - (asset_cap)
            Alloted_percent[i] = asset_cap #if a percent exceeds cap, we limit it and calc residue

            insert_index = i
            balanced_percent = Alloted_percent[i]
            Alloted_percent.pop(i) #saving index value pair and then popping capped item

            #residue calc
            Alloted_percent = residue_redistribute(Alloted_percent, residue_percent) 

            recursive = True
            break #no need to continue loop. popped item ensures we wont tack on residue to already calc'd
     
    if recursive:
        Alloted_percent = recursive_rebalancing(Alloted_percent, asset_cap) #eventually loop will run into 1 item or no item exceeding cap. that's how it exits recursion
        Alloted_percent.insert(insert_index, balanced_percent) #only happens once all inner loops have been checked. then recursive func works backwards and reinserts items 

    return Alloted_percent

def residue_redistribute(Alloted_percent: List[float], residue: float):
    ratio_total: float = 0
    new_ratio: List[float] = []

    for percent in Alloted_percent:
        ratio_total += percent #calcs new grand mcap
    for percent in Alloted_percent:
        new_ratio.append((percent/ratio_total)*100) #list with less items now has a new ratio based on 1 (100%)

    for i in range(len(Alloted_percent)):
        Alloted_percent[i] = (residue*(new_ratio[i]/100)) + Alloted_percent[i] #takes remainder from asset_cap of popped item and tacks it on with calc'd ratio

    return Alloted_percent