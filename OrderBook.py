from uuid import UUID
from typing import List

from pydantic import BaseModel

class Order:
    order_id: UUID
    quantity: str

    def __init__(self, data):
        self.order_id = data["orderId"]
        self.quantity = data["quantity"]


class Ask:
    price: str
    orders: List[Order]

    def __init__(self, data):
        self.price = data["Price"]
        self.orders = data.get("Orders")


class Data:
    last_change: int
    asks: List[Ask]
    bids: List[Ask]
    sequence_number: int
    checksum: int

    def __init__(self, data):
        self.last_change = data["LastChange"]
        self.asks = data.get("Asks")
        self.bids = data.get("Bids")
        self.sequence_number = data["SequenceNumber"]
        self.checksum = data["Checksum"]

#Order book family
class OrderBook:
    type: str
    currency_pair_symbol: str
    data: Data

    def __init__(self, data):
        self.type = data["type"]
        self.currency_pair_symbol = data["currencyPairSymbol"] 
        self.data = data["data"]

#Mini book
class MiniBook:
    price: float
    quantity: float

    def __init__(self, price, quantity):
        self.price = price
        self.quantity = quantity

#Binance json
class OrderBook_MemeCoin:
    last_update_id: int
    bids: List[List[str]]
    asks: List[List[str]]
    
    def __init__(self, data):
        self.last_update_id = data["lastUpdateId"]
        self.bids = data["bids"]
        self.asks = data["asks"]

class Ticker(BaseModel):
    symbol: str
    mcap: float
    price: float

class BalancedOutput(BaseModel):
    symbol: str
    amount: float
    zar_value: float
    percent: float