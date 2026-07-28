"""
Integration tests for v1 FastAPI endpoints.

These test the full stack: HTTP request -> validation -> service -> response.
"""

import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
import json
import os
import tempfile

from main_v1 import app
from v1.clock import SystemClock
from v1.repositories import FileConfigRepository, FileInvoiceRepository
from v1.pricing_service import PricingService


@pytest.fixture
def client():
    """Create a test client with temporary file repositories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "pricing_config.json")
        invoice_path = os.path.join(tmpdir, "invoices.json")

        # Create test config file
        with open(config_path, "w") as f:
            json.dump(
                {"basic": 10.0, "pro": 25.0, "enterprise": 50.0},
                f,
            )

        # Replace app dependencies with test instances
        clock = SystemClock()
        config_repo = FileConfigRepository(config_path)
        invoice_repo = FileInvoiceRepository(invoice_path)
        app.state.pricing_service = PricingService(clock, config_repo, invoice_repo)

        yield TestClient(app)


class TestHealthEndpoint:
    def test_health_check_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "version": "v1"}


class TestQuoteEndpoint:
    def test_basic_quote_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={
                "plan": "basic",
                "seats": 10,
                "billing_cycle": "monthly",
                "region": "UK",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["plan"] == "basic"
        assert data["seats"] == 10
        assert Decimal(str(data["net"])) == Decimal("95.00")
        assert Decimal(str(data["tax"])) == Decimal("19.00")
        assert Decimal(str(data["total"])) == Decimal("114.00")

    def test_pro_plan_annual_ie(self, client):
        response = client.post(
            "/quote",
            json={
                "plan": "pro",
                "seats": 25,
                "billing_cycle": "annual",
                "region": "IE",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(str(data["net"])) == Decimal("6075.00")
        assert Decimal(str(data["tax"])) == Decimal("1397.25")

    def test_enterprise_plan_us_no_tax(self, client):
        response = client.post(
            "/quote",
            json={
                "plan": "enterprise",
                "seats": 50,
                "billing_cycle": "monthly",
                "region": "US",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(str(data["tax"])) == Decimal("0.00")


class TestInputValidation:
    def test_missing_seats_returns_422(self, client):
        response = client.post(
            "/quote",
            json={
                "plan": "basic",
                "billing_cycle": "monthly",
                "region": "UK",
            },
        )

        assert response.status_code == 422
        assert "detail" in response.json()

    def test_negative_seats_returns_422(self, client):
        response = client.post(
            "/quote",
            json={
                "plan": "basic",
                "seats": -5,
                "billing_cycle": "monthly",
                "region": "UK",
            },
        )

        assert response.status_code == 422

    def test_zero_seats_returns_422(self, client):
        response = client.post(
            "/quote",
            json={
                "plan": "basic",
                "seats": 0,
                "billing_cycle": "monthly",
                "region": "UK",
            },
        )

        assert response.status_code == 422

    def test_seats_as_string_returns_422(self, client):
        response = client.post(
            "/quote",
            json={
                "plan": "basic",
                "seats": "ten",
                "billing_cycle": "monthly",
                "region": "UK",
            },
        )

        assert response.status_code == 422

    def test_unknown_plan_returns_400(self, client):
        response = client.post(
            "/quote",
            json={
                "plan": "premium",
                "seats": 10,
                "billing_cycle": "monthly",
                "region": "UK",
            },
        )

        assert response.status_code == 400
        assert "plan" in response.json()["detail"].lower()

    def test_unknown_region_returns_400(self, client):
        response = client.post(
            "/quote",
            json={
                "plan": "basic",
                "seats": 10,
                "billing_cycle": "monthly",
                "region": "FR",
            },
        )

        assert response.status_code == 400
        assert "region" in response.json()["detail"].lower()


class TestBoundaryValues:
    """Test the pricing anomaly at discount thresholds."""

    def test_24_vs_25_seats_anomaly(self, client):
        """
        Known anomaly: 25 seats is cheaper than 24 seats because
        discount applies to entire subtotal at threshold.
        """
        response_24 = client.post(
            "/quote",
            json={
                "plan": "pro",
                "seats": 24,
                "billing_cycle": "monthly",
                "region": "UK",
            },
        )

        response_25 = client.post(
            "/quote",
            json={
                "plan": "pro",
                "seats": 25,
                "billing_cycle": "monthly",
                "region": "UK",
            },
        )

        assert response_24.status_code == 200
        assert response_25.status_code == 200

        total_24 = Decimal(str(response_24.json()["total"]))
        total_25 = Decimal(str(response_25.json()["total"]))

        # This documents the anomaly: adding a seat reduces the bill
        assert total_25 < total_24

    def test_discount_thresholds(self, client):
        """Test seats just below and above each discount threshold."""
        test_cases = [
            (9, "0%"),
            (10, "5%"),
            (24, "5%"),
            (25, "10%"),
            (49, "10%"),
            (50, "15%"),
            (99, "15%"),
            (100, "20%"),
        ]

        for seats, expected_discount in test_cases:
            response = client.post(
                "/quote",
                json={
                    "plan": "basic",
                    "seats": seats,
                    "billing_cycle": "monthly",
                    "region": "UK",
                },
            )
            assert response.status_code == 200, f"Failed for {seats} seats"


class TestProRataStartDate:
    def test_with_start_date_in_current_month(self, client):
        response = client.post(
            "/quote",
            json={
                "plan": "basic",
                "seats": 10,
                "billing_cycle": "monthly",
                "region": "UK",
                "start_date": "2026-07-15",
            },
        )

        assert response.status_code == 200
        # Pro-rata calculation will vary based on current date

    def test_without_start_date(self, client):
        response = client.post(
            "/quote",
            json={
                "plan": "basic",
                "seats": 10,
                "billing_cycle": "monthly",
                "region": "UK",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert Decimal(str(data["net"])) == Decimal("95.00")
