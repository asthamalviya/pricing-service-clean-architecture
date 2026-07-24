"""
Characterisation tests for QuickQuote v0.

These tests lock in the current behaviour of v0, including known bugs and anomalies.
Their purpose is to prove that subsequent refactoring preserves business logic.

Test coverage:
- All volume discount boundaries: 9, 10, 24, 25, 49, 50, 99, 100 seats
- All plans: basic (£10), pro (£25), enterprise (£50)
- All billing cycles: monthly, annual (10% discount)
- All regions: UK (20%), IE (23%), DE (19%), US (0%)
- Known pricing anomaly at 25 pro seats (documented below)
- Error cases: unknown plan, unknown region
"""

import pytest


class TestVolumeBoundaries:
    """Test volume discount thresholds across all plans."""

    def test_basic_9_seats_no_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "basic", "seats": 9, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 90.0
        assert data["tax"] == 18.0
        assert data["total"] == 108.0

    def test_basic_10_seats_5pct_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "basic", "seats": 10, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 95.0
        assert data["tax"] == 19.0
        assert data["total"] == 114.0

    def test_basic_24_seats_5pct_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "basic", "seats": 24, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 228.0
        assert data["tax"] == 45.6
        assert data["total"] == 273.6

    def test_basic_25_seats_10pct_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "basic", "seats": 25, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 225.0
        assert data["tax"] == 45.0
        assert data["total"] == 270.0

    def test_basic_49_seats_10pct_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "basic", "seats": 49, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 441.0
        assert data["tax"] == 88.2
        assert data["total"] == 529.2

    def test_basic_50_seats_15pct_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "basic", "seats": 50, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 425.0
        assert data["tax"] == 85.0
        assert data["total"] == 510.0

    def test_basic_99_seats_15pct_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "basic", "seats": 99, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 841.5
        assert data["tax"] == 168.3
        assert data["total"] == 1009.8

    def test_basic_100_seats_20pct_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "basic", "seats": 100, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 800.0
        assert data["tax"] == 160.0
        assert data["total"] == 960.0


class TestProPlanBoundaries:
    """Test pro plan across volume boundaries."""

    def test_pro_9_seats_no_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "pro", "seats": 9, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 225.0
        assert data["tax"] == 45.0
        assert data["total"] == 270.0

    def test_pro_10_seats_5pct_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "pro", "seats": 10, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 237.5
        assert data["tax"] == 47.5
        assert data["total"] == 285.0

    def test_pro_24_seats_5pct_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "pro", "seats": 24, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 570.0
        assert data["tax"] == 114.0
        assert data["total"] == 684.0

    def test_pro_25_seats_10pct_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "pro", "seats": 25, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 562.5
        assert data["tax"] == 112.5
        assert data["total"] == 675.0

    def test_pro_49_seats_10pct_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "pro", "seats": 49, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 1102.5
        assert data["tax"] == 220.5
        assert data["total"] == 1323.0

    def test_pro_50_seats_15pct_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "pro", "seats": 50, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 1062.5
        assert data["tax"] == 212.5
        assert data["total"] == 1275.0

    def test_pro_99_seats_15pct_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "pro", "seats": 99, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 2103.75
        assert data["tax"] == 420.75
        assert data["total"] == 2524.5

    def test_pro_100_seats_20pct_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "pro", "seats": 100, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 2000.0
        assert data["tax"] == 400.0
        assert data["total"] == 2400.0


class TestEnterprisePlanBoundaries:
    """Test enterprise plan across volume boundaries."""

    def test_enterprise_9_seats_no_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "enterprise", "seats": 9, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 450.0
        assert data["tax"] == 90.0
        assert data["total"] == 540.0

    def test_enterprise_10_seats_5pct_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "enterprise", "seats": 10, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 475.0
        assert data["tax"] == 95.0
        assert data["total"] == 570.0

    def test_enterprise_25_seats_10pct_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "enterprise", "seats": 25, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 1125.0
        assert data["tax"] == 225.0
        assert data["total"] == 1350.0

    def test_enterprise_50_seats_15pct_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "enterprise", "seats": 50, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 2125.0
        assert data["tax"] == 425.0
        assert data["total"] == 2550.0

    def test_enterprise_100_seats_20pct_discount_uk_monthly(self, client):
        response = client.post(
            "/quote",
            json={"plan": "enterprise", "seats": 100, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["net"] == 4000.0
        assert data["tax"] == 800.0
        assert data["total"] == 4800.0


class TestKnownAnomaly:
    """
    KNOWN PRICING ANOMALY: 25 pro seats costs less than 24 pro seats.

    This is a business logic issue in v0 caused by the 10% volume discount
    threshold at 25 seats. When a customer adds one seat from 24 to 25,
    they cross the discount boundary and their total price decreases.

    24 seats: 25 × 24 = 600, 5% discount = 570, 20% tax = 684 total
    25 seats: 25 × 25 = 625, 10% discount = 562.5, 20% tax = 675 total

    This test captures the anomaly for documentation purposes. It should
    NOT be silently fixed during refactoring—it requires a business decision
    about whether to adjust the discount thresholds or pricing tiers.
    """

    def test_anomaly_25_pro_seats_cheaper_than_24(self, client):
        response_24 = client.post(
            "/quote",
            json={"plan": "pro", "seats": 24, "billing_cycle": "monthly", "region": "UK"},
        )
        response_25 = client.post(
            "/quote",
            json={"plan": "pro", "seats": 25, "billing_cycle": "monthly", "region": "UK"},
        )

        total_24 = response_24.json()["total"]
        total_25 = response_25.json()["total"]

        assert total_24 == 684.0
        assert total_25 == 675.0
        assert total_25 < total_24, "25 seats should be cheaper than 24 (known anomaly)"


class TestAllRegions:
    """Test tax calculation across all supported regions."""

    def test_uk_20pct_tax(self, client):
        response = client.post(
            "/quote",
            json={"plan": "basic", "seats": 10, "billing_cycle": "monthly", "region": "UK"},
        )
        data = response.json()
        assert data["net"] == 95.0
        assert data["tax"] == 19.0
        assert data["total"] == 114.0

    def test_ie_23pct_tax(self, client):
        response = client.post(
            "/quote",
            json={"plan": "basic", "seats": 10, "billing_cycle": "monthly", "region": "IE"},
        )
        data = response.json()
        assert data["net"] == 95.0
        assert data["tax"] == 21.85
        assert data["total"] == 116.85

    def test_de_19pct_tax(self, client):
        response = client.post(
            "/quote",
            json={"plan": "basic", "seats": 10, "billing_cycle": "monthly", "region": "DE"},
        )
        data = response.json()
        assert data["net"] == 95.0
        assert data["tax"] == 18.05
        assert data["total"] == 113.05

    def test_us_0pct_tax(self, client):
        response = client.post(
            "/quote",
            json={"plan": "basic", "seats": 10, "billing_cycle": "monthly", "region": "US"},
        )
        data = response.json()
        assert data["net"] == 95.0
        assert data["tax"] == 0.0
        assert data["total"] == 95.0


class TestAnnualBilling:
    """Test annual billing cycle with 10% discount."""

    def test_basic_annual_10pct_discount_uk(self, client):
        response = client.post(
            "/quote",
            json={"plan": "basic", "seats": 10, "billing_cycle": "annual", "region": "UK"},
        )
        data = response.json()
        assert data["net"] == 1026.0
        assert data["tax"] == 205.2
        assert data["total"] == 1231.2

    def test_pro_25_seats_annual_uk(self, client):
        response = client.post(
            "/quote",
            json={"plan": "pro", "seats": 25, "billing_cycle": "annual", "region": "UK"},
        )
        data = response.json()
        assert data["net"] == 6075.0
        assert data["tax"] == 1215.0
        assert data["total"] == 7290.0

    def test_enterprise_50_seats_annual_de(self, client):
        response = client.post(
            "/quote",
            json={"plan": "enterprise", "seats": 50, "billing_cycle": "annual", "region": "DE"},
        )
        data = response.json()
        assert data["net"] == 22950.0
        assert data["tax"] == 4360.5
        assert data["total"] == 27310.5


class TestProRata:
    """
    Test pro-rata calculation for mid-month starts.

    NOTE: v0 uses datetime.now() internally, so these tests will only pass
    if run in the same month as the start_date. This is a known limitation
    that will be fixed in v1 by injecting a clock interface.
    """

    def test_monthly_prorata_first_day(self, client):
        response = client.post(
            "/quote",
            json={
                "plan": "basic",
                "seats": 10,
                "billing_cycle": "monthly",
                "region": "UK",
                "start_date": "2026-07-01",
            },
        )
        data = response.json()
        assert data["net"] == 95.0
        assert data["tax"] == 19.0
        assert data["total"] == 114.0

    def test_monthly_prorata_mid_month(self, client):
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
        data = response.json()
        assert data["net"] == 52.1
        assert data["tax"] == 10.42
        assert data["total"] == 62.52

    def test_monthly_prorata_last_day(self, client):
        response = client.post(
            "/quote",
            json={
                "plan": "basic",
                "seats": 10,
                "billing_cycle": "monthly",
                "region": "UK",
                "start_date": "2026-07-31",
            },
        )
        data = response.json()
        assert data["net"] == 3.06
        assert data["tax"] == 0.61
        assert data["total"] == 3.67


class TestErrorCases:
    """Test error handling for invalid inputs."""

    def test_unknown_plan(self, client):
        response = client.post(
            "/quote",
            json={"plan": "premium", "seats": 10, "billing_cycle": "monthly", "region": "UK"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"] == "unknown plan"

    def test_unknown_region(self, client):
        response = client.post(
            "/quote",
            json={"plan": "basic", "seats": 10, "billing_cycle": "monthly", "region": "FR"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"] == "unknown region"
