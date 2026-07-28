"""
PricingService orchestrates the quote calculation.

This is the heart of v1: it takes dependencies via constructor (clock,
repositories, strategies) and produces a quote without any knowledge of HTTP.
"""

from decimal import Decimal
import calendar
from datetime import datetime

from v1.clock import Clock
from v1.repositories import ConfigRepository, InvoiceRepository
from v1.pricing_rules import PlanPricer, VolumeDiscountStrategy, TaxCalculator
from v1.models import QuoteRequest, Quote


class PricingService:
    def __init__(
        self,
        clock: Clock,
        config_repo: ConfigRepository,
        invoice_repo: InvoiceRepository,
    ):
        self._clock = clock
        self._config_repo = config_repo
        self._invoice_repo = invoice_repo

        plan_prices = config_repo.get_plan_prices()
        self._plan_pricer = PlanPricer(plan_prices)
        self._volume_discount = VolumeDiscountStrategy()
        self._tax_calculator = TaxCalculator()

    def calculate_quote(self, request: QuoteRequest) -> Quote:
        unit_price = self._plan_pricer.get_unit_price(request.plan)

        subtotal = unit_price * request.seats

        discount_rate = self._volume_discount.get_discount_rate(request.seats)
        discounted = subtotal * (Decimal("1") - discount_rate)

        if request.billing_cycle == "annual":
            discounted = discounted * 12 * Decimal("0.90")

        if request.billing_cycle == "monthly" and request.start_date:
            current_date = self._clock.today()
            if (
                request.start_date.year == current_date.year
                and request.start_date.month == current_date.month
            ):
                days_in_month = calendar.monthrange(
                    current_date.year, current_date.month
                )[1]
                remaining_days = days_in_month - request.start_date.day + 1
                discounted = discounted * (Decimal(remaining_days) / Decimal(days_in_month))

        tax_rate = self._tax_calculator.get_tax_rate(request.region)
        tax = discounted * tax_rate

        net = self._round_currency(discounted)
        tax_amount = self._round_currency(tax)
        total = net + tax_amount

        quote = Quote(
            plan=request.plan,
            seats=request.seats,
            billing_cycle=request.billing_cycle,
            region=request.region,
            net=net,
            tax=tax_amount,
            total=total,
        )

        self._invoice_repo.save_invoice(
            {
                **quote.model_dump(),
                "issued_at": datetime.now().isoformat(),
            }
        )

        return quote

    def _round_currency(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"))
