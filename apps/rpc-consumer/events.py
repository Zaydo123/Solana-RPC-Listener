"""
events.py
Structured format for events such as new pair, swap, and burn
"""

from solders.pubkey import Pubkey
from classes import Transaction
from typing import Dict, Any
from typing import List
import json
import time

class Event:
    def __init__(self, event_type: str, data: Dict[str, Any], block_time: float = time.time()):
        self.event_type = event_type
        self.block_time = block_time
        self.data = data

    def to_json(self):
        return json.dumps({"event_type": self.event_type, "data": self.data})

    @staticmethod
    def from_json(json_data):
        data = json.loads(json_data)
        return Event(data["event_type"], data["data"])
    
    def __str__(self):
        return self.to_json()
    
    def __eq__(self, other):
        return self.event_type == other.event_type and self.data == other.data
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
class NewPairEvent(Event):
    def __init__(self, base_token: str, quote_token: str, base_pool_account: str, quote_pool_account: str, block_time: float = time.time()):
        self.base_token = base_token
        self.quote_token = quote_token
        self.base_pool_account = base_pool_account
        self.quote_pool_account = quote_pool_account
        self.block_time = block_time
        super().__init__("new_pair", {"base_token": base_token, "quote_token": quote_token, "base_pool_account": base_pool_account, "quote_pool_account": quote_pool_account})
    
    def __str__(self):
        return json.dumps({"event_type": self.event_type, "data": {"base_token": self.base_token, "quote_token": self.quote_token, "base_pool_account": self.base_pool_account, "quote_pool_account": self.quote_pool_account, "block_time": self.block_time}})
    
    def __eq__(self, other):
        return self.base_token == other.base_token and self.quote_token == other.quote_token and self.base_pool_account == other.base_pool_account and self.quote_pool_account == other.quote_pool_account
    
    def __ne__(self, other):
        return not self.__eq__(other)
    

class SwapEvent(Event):
    def __init__(self, transaction: Transaction):
        self.transaction = transaction
        if transaction is None:
            raise ValueError("Transaction cannot be None")
        super().__init__("swap", {"transaction": transaction.to_json()})

    def __str__(self):
        return json.dumps({"event_type": self.event_type, "data": {"transaction": self.transaction.to_json()}})
    
    def __eq__(self, other):
        return self.transaction == other.transaction
        
    def __ne__(self, other):
        return not self.__eq__(other)
    

class BurnEvent(Event):
    def __init__(self, token: Pubkey, account: Pubkey, authority: Pubkey, amount: float, block_time: float = time.time()):
        self.token = token
        self.account = account # the token account that burned the token
        self.authority = authority # usually the token account owner
        self.amount = amount
        self.block_time = block_time
        super().__init__("burn", {"token": str(token), "amount": amount})
        
    def __str__(self):
        return json.dumps({"event_type": self.event_type, "data": {"token": self.token, "account": self.account, "authority": self.authority, "amount": self.amount, "block_time": self.block_time}})

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.token == other.token and self.amount == other.amount and self.account == other.account and self.authority == other.authority and self.block_time == other.block_time

    def __ne__(self, other):
        return not self.__eq__(other)

