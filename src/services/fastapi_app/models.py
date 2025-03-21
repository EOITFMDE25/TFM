from pydantic import BaseModel, Field
from typing import List

class Item(BaseModel):
    name: str
    quantity: str
    unit_price: str
    total_price: str
    category: str

class Tax(BaseModel):
    name: str
    amount: str

class Ticket(BaseModel):
    supermarket: str
    date: str
    time: str
    location: str
    items: List[Item]
    subtotal: float
    taxes: List[Tax]
    total: float
    payment_method: str
    currency: str

class SupermarketCategoryResult(BaseModel):
    supermarket: str
    category: str
    total_spent: float
    num_items: int


class HTTPExceptionModel(BaseModel):
    detail: str = Field(description="Error message", example="Client id not found")