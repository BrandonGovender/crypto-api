from uuid import UUID
from typing import List


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


class OrderBook:
    type: str
    currency_pair_symbol: str
    data: Data

    def __init__(self, data):
        self.type = data["type"]
        self.currency_pair_symbol = data["currencyPairSymbol"] 
        self.data = data["data"]

class MiniBook:
    price: float
    quantity: float

    def __init__(self, price, quantity):
        self.price = price
        self.quantity = quantity

