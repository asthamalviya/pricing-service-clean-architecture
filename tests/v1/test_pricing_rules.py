"""
Unit tests for pricing rule strategies.

Testing technique: Boundary value analysis and equivalence partitioning.
Each discount threshold is tested at boundary-1, boundary, boundary+1.
"""

import pytest
from decimal import Decimal
from v1.pricing_rules import (
    PlanPricer,
    VolumeDiscountStrategy,
    TaxCalculator,
    UnknownPlanError,
    UnknownRegionError,
)


class TestPlanPricer:
    def test_returns_correct_price_for_each_plan(self):
        prices = {
            "basic": Decimal("10"),
            "pro": Decimal("25"),
            "enterprise": Decimal("50"),
        }
        pricer = PlanPricer(prices)

        assert pricer.get_unit_price("basic") == Decimal("10")
        assert pricer.get_unit_price("pro") == Decimal("25")
        assert pricer.get_unit_price("enterprise") == Decimal("50")

    def test_raises_on_unknown_plan(self):
        pricer = PlanPricer({"basic": Decimal("10")})

        with pytest.raises(UnknownPlanError, match="Unknown plan: premium"):
            pricer.get_unit_price("premium")


class TestVolumeDiscountStrategy:
    def test_no_discount_below_10_seats(self):
        strategy = VolumeDiscountStrategy()

        assert strategy.get_discount_rate(1) == Decimal("0.0")
        assert strategy.get_discount_rate(5) == Decimal("0.0")
        assert strategy.get_discount_rate(9) == Decimal("0.0")

    def test_5pct_discount_at_10_to_24_seats(self):
        strategy = VolumeDiscountStrategy()

        assert strategy.get_discount_rate(10) == Decimal("0.05")
        assert strategy.get_discount_rate(15) == Decimal("0.05")
        assert strategy.get_discount_rate(24) == Decimal("0.05")

    def test_10pct_discount_at_25_to_49_seats(self):
        strategy = VolumeDiscountStrategy()

        assert strategy.get_discount_rate(25) == Decimal("0.10")
        assert strategy.get_discount_rate(30) == Decimal("0.10")
        assert strategy.get_discount_rate(49) == Decimal("0.10")

    def test_15pct_discount_at_50_to_99_seats(self):
        strategy = VolumeDiscountStrategy()

        assert strategy.get_discount_rate(50) == Decimal("0.15")
        assert strategy.get_discount_rate(75) == Decimal("0.15")
        assert strategy.get_discount_rate(99) == Decimal("0.15")

    def test_20pct_discount_at_100_plus_seats(self):
        strategy = VolumeDiscountStrategy()

        assert strategy.get_discount_rate(100) == Decimal("0.20")
        assert strategy.get_discount_rate(500) == Decimal("0.20")
        assert strategy.get_discount_rate(1000) == Decimal("0.20")

    def test_boundary_values(self):
        strategy = VolumeDiscountStrategy()

        assert strategy.get_discount_rate(9) == Decimal("0.0")
        assert strategy.get_discount_rate(10) == Decimal("0.05")

        assert strategy.get_discount_rate(24) == Decimal("0.05")
        assert strategy.get_discount_rate(25) == Decimal("0.10")

        assert strategy.get_discount_rate(49) == Decimal("0.10")
        assert strategy.get_discount_rate(50) == Decimal("0.15")

        assert strategy.get_discount_rate(99) == Decimal("0.15")
        assert strategy.get_discount_rate(100) == Decimal("0.20")


class TestTaxCalculator:
    def test_returns_correct_rate_for_each_region(self):
        calculator = TaxCalculator()

        assert calculator.get_tax_rate("UK") == Decimal("0.20")
        assert calculator.get_tax_rate("IE") == Decimal("0.23")
        assert calculator.get_tax_rate("DE") == Decimal("0.19")
        assert calculator.get_tax_rate("US") == Decimal("0.0")

    def test_raises_on_unknown_region(self):
        calculator = TaxCalculator()

        with pytest.raises(UnknownRegionError, match="Unknown region: FR"):
            calculator.get_tax_rate("FR")
