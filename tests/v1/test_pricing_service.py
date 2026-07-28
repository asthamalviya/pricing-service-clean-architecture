"""
Unit tests for PricingService.

Testing techniques:
- White-box: test each calculation branch (volume, annual, prorata, tax)
- Boundary: test discount thresholds and date boundaries
- Determinism: use FixedClock for reproducible prorata calculations
"""

import pytest
from decimal import Decimal
from datetime import date

from v1.pricing_service import PricingService
from v1.clock import FixedClock
from v1.repositories import InMemoryConfigRepository, InMemoryInvoiceRepository
from v1.models import QuoteRequest
from v1.pricing_rules import UnknownPlanError, UnknownRegionError


@pytest.fixture
def service():
    clock = FixedClock(date(2026, 7, 15))
    config_repo = InMemoryConfigRepository(
        {"basic": Decimal("10"), "pro": Decimal("25"), "enterprise": Decimal("50")}
    )
    invoice_repo = InMemoryInvoiceRepository()
    return PricingService(clock, config_repo, invoice_repo)


class TestBasicCalculation:
    def test_basic_plan_no_discount_uk_monthly(self, service):
        request = QuoteRequest(
            plan="basic", seats=9, billing_cycle="monthly", region="UK"
        )
        quote = service.calculate_quote(request)

        assert quote.net == Decimal("90.00")
        assert quote.tax == Decimal("18.00")
        assert quote.total == Decimal("108.00")

    def test_pro_plan_no_discount_us_monthly(self, service):
        request = QuoteRequest(
            plan="pro", seats=5, billing_cycle="monthly", region="US"
        )
        quote = service.calculate_quote(request)

        assert quote.net == Decimal("125.00")
        assert quote.tax == Decimal("0.00")
        assert quote.total == Decimal("125.00")


class TestVolumeDiscounts:
    def test_10_seats_gets_5pct_discount(self, service):
        request = QuoteRequest(
            plan="basic", seats=10, billing_cycle="monthly", region="UK"
        )
        quote = service.calculate_quote(request)

        assert quote.net == Decimal("95.00")

    def test_25_seats_gets_10pct_discount(self, service):
        request = QuoteRequest(
            plan="basic", seats=25, billing_cycle="monthly", region="UK"
        )
        quote = service.calculate_quote(request)

        assert quote.net == Decimal("225.00")

    def test_50_seats_gets_15pct_discount(self, service):
        request = QuoteRequest(
            plan="basic", seats=50, billing_cycle="monthly", region="UK"
        )
        quote = service.calculate_quote(request)

        assert quote.net == Decimal("425.00")

    def test_100_seats_gets_20pct_discount(self, service):
        request = QuoteRequest(
            plan="basic", seats=100, billing_cycle="monthly", region="UK"
        )
        quote = service.calculate_quote(request)

        assert quote.net == Decimal("800.00")


class TestAnnualBilling:
    def test_annual_billing_applies_10pct_discount(self, service):
        request = QuoteRequest(
            plan="basic", seats=10, billing_cycle="annual", region="UK"
        )
        quote = service.calculate_quote(request)

        assert quote.net == Decimal("1026.00")
        assert quote.tax == Decimal("205.20")
        assert quote.total == Decimal("1231.20")

    def test_annual_applies_to_discounted_price(self, service):
        request = QuoteRequest(
            plan="pro", seats=25, billing_cycle="annual", region="UK"
        )
        quote = service.calculate_quote(request)

        assert quote.net == Decimal("6075.00")


class TestProRata:
    def test_prorata_first_day_of_month(self):
        clock = FixedClock(date(2026, 7, 1))
        config_repo = InMemoryConfigRepository({"basic": Decimal("10")})
        invoice_repo = InMemoryInvoiceRepository()
        service = PricingService(clock, config_repo, invoice_repo)

        request = QuoteRequest(
            plan="basic",
            seats=10,
            billing_cycle="monthly",
            region="UK",
            start_date=date(2026, 7, 1),
        )
        quote = service.calculate_quote(request)

        assert quote.net == Decimal("95.00")
        assert quote.total == Decimal("114.00")

    def test_prorata_mid_month(self):
        clock = FixedClock(date(2026, 7, 15))
        config_repo = InMemoryConfigRepository({"basic": Decimal("10")})
        invoice_repo = InMemoryInvoiceRepository()
        service = PricingService(clock, config_repo, invoice_repo)

        request = QuoteRequest(
            plan="basic",
            seats=10,
            billing_cycle="monthly",
            region="UK",
            start_date=date(2026, 7, 15),
        )
        quote = service.calculate_quote(request)

        assert quote.net == Decimal("52.10")
        assert quote.tax == Decimal("10.42")
        assert quote.total == Decimal("62.52")

    def test_prorata_last_day_of_month(self):
        clock = FixedClock(date(2026, 7, 31))
        config_repo = InMemoryConfigRepository({"basic": Decimal("10")})
        invoice_repo = InMemoryInvoiceRepository()
        service = PricingService(clock, config_repo, invoice_repo)

        request = QuoteRequest(
            plan="basic",
            seats=10,
            billing_cycle="monthly",
            region="UK",
            start_date=date(2026, 7, 31),
        )
        quote = service.calculate_quote(request)

        assert quote.net == Decimal("3.06")
        assert quote.tax == Decimal("0.61")
        assert quote.total == Decimal("3.67")

    def test_prorata_not_applied_for_different_month(self):
        clock = FixedClock(date(2026, 7, 15))
        config_repo = InMemoryConfigRepository({"basic": Decimal("10")})
        invoice_repo = InMemoryInvoiceRepository()
        service = PricingService(clock, config_repo, invoice_repo)

        request = QuoteRequest(
            plan="basic",
            seats=10,
            billing_cycle="monthly",
            region="UK",
            start_date=date(2026, 8, 1),
        )
        quote = service.calculate_quote(request)

        assert quote.net == Decimal("95.00")


class TestTaxRates:
    def test_uk_20pct_tax(self, service):
        request = QuoteRequest(
            plan="basic", seats=10, billing_cycle="monthly", region="UK"
        )
        quote = service.calculate_quote(request)

        assert quote.tax == Decimal("19.00")

    def test_ie_23pct_tax(self, service):
        request = QuoteRequest(
            plan="basic", seats=10, billing_cycle="monthly", region="IE"
        )
        quote = service.calculate_quote(request)

        assert quote.tax == Decimal("21.85")

    def test_de_19pct_tax(self, service):
        request = QuoteRequest(
            plan="basic", seats=10, billing_cycle="monthly", region="DE"
        )
        quote = service.calculate_quote(request)

        assert quote.tax == Decimal("18.05")

    def test_us_0pct_tax(self, service):
        request = QuoteRequest(
            plan="basic", seats=10, billing_cycle="monthly", region="US"
        )
        quote = service.calculate_quote(request)

        assert quote.tax == Decimal("0.00")


class TestErrorHandling:
    def test_unknown_plan_raises_error(self, service):
        request = QuoteRequest(
            plan="premium", seats=10, billing_cycle="monthly", region="UK"
        )

        with pytest.raises(UnknownPlanError):
            service.calculate_quote(request)

    def test_unknown_region_raises_error(self, service):
        request = QuoteRequest(
            plan="basic", seats=10, billing_cycle="monthly", region="FR"
        )

        with pytest.raises(UnknownRegionError):
            service.calculate_quote(request)


class TestInvoicePersistence:
    def test_saves_invoice_to_repository(self):
        clock = FixedClock(date(2026, 7, 15))
        config_repo = InMemoryConfigRepository({"basic": Decimal("10")})
        invoice_repo = InMemoryInvoiceRepository()
        service = PricingService(clock, config_repo, invoice_repo)

        request = QuoteRequest(
            plan="basic", seats=10, billing_cycle="monthly", region="UK"
        )
        service.calculate_quote(request)

        invoices = invoice_repo.get_all_invoices()
        assert len(invoices) == 1
        assert invoices[0]["plan"] == "basic"
        assert invoices[0]["seats"] == 10
        assert "issued_at" in invoices[0]
