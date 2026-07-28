"""
Pydantic models for request and response validation.
"""

from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date
from typing import Optional


class QuoteRequest(BaseModel):
    plan: str
    seats: int = Field(gt=0, description="Number of seats (must be positive)")
    billing_cycle: str
    region: str
    start_date: Optional[date] = None


class Quote(BaseModel):
    plan: str
    seats: int
    billing_cycle: str
    region: str
    net: Decimal
    tax: Decimal
    total: Decimal
