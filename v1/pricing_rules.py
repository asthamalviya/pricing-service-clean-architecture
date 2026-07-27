"""
Pricing rules as strategy objects.

Replaces v0's three separate if/elif chains with declarative data structures.
Adding a new plan, discount tier, or tax region requires only adding data,
not editing branching logic.
"""

from decimal import Decimal
from typing import Dict


class UnknownPlanError(Exception):
    pass


class UnknownRegionError(Exception):
    pass


class PlanPricer:
    def __init__(self, plan_prices: Dict[str, Decimal]):
        self._prices = plan_prices

    def get_unit_price(self, plan: str) -> Decimal:
        if plan not in self._prices:
            raise UnknownPlanError(f"Unknown plan: {plan}")
        return self._prices[plan]


class VolumeDiscountStrategy:
    def __init__(self):
        self._tiers = [
            (100, Decimal("0.20")),
            (50, Decimal("0.15")),
            (25, Decimal("0.10")),
            (10, Decimal("0.05")),
        ]

    def get_discount_rate(self, seats: int) -> Decimal:
        for threshold, rate in self._tiers:
            if seats >= threshold:
                return rate
        return Decimal("0.0")


class TaxCalculator:
    def __init__(self):
        self._rates = {
            "UK": Decimal("0.20"),
            "IE": Decimal("0.23"),
            "DE": Decimal("0.19"),
            "US": Decimal("0.0"),
        }

    def get_tax_rate(self, region: str) -> Decimal:
        if region not in self._rates:
            raise UnknownRegionError(f"Unknown region: {region}")
        return self._rates[region]
