"""
Unit tests for repository implementations.

Testing technique: White-box unit testing with equivalence partitioning.
Tests both file-based and in-memory implementations.
"""

from decimal import Decimal
import tempfile
import json
import os
from v1.repositories import (
    FileConfigRepository,
    FileInvoiceRepository,
    InMemoryConfigRepository,
    InMemoryInvoiceRepository,
)


class TestFileConfigRepository:
    def test_loads_plan_prices_from_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"basic": 10, "pro": 25, "enterprise": 50}, f)
            config_path = f.name

        try:
            repo = FileConfigRepository(config_path)
            prices = repo.get_plan_prices()

            assert prices == {
                "basic": Decimal("10"),
                "pro": Decimal("25"),
                "enterprise": Decimal("50"),
            }
        finally:
            os.unlink(config_path)

    def test_returns_decimal_not_float(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"basic": 10.50}, f)
            config_path = f.name

        try:
            repo = FileConfigRepository(config_path)
            prices = repo.get_plan_prices()

            assert isinstance(prices["basic"], Decimal)
            assert prices["basic"] == Decimal("10.50")
        finally:
            os.unlink(config_path)


class TestFileInvoiceRepository:
    def test_saves_invoice_to_new_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            invoice_path = f.name

        try:
            os.unlink(invoice_path)

            repo = FileInvoiceRepository(invoice_path)
            repo.save_invoice({"plan": "basic", "total": 100})

            assert os.path.exists(invoice_path)
            invoices = repo.get_all_invoices()
            assert len(invoices) == 1
            assert invoices[0]["plan"] == "basic"
        finally:
            if os.path.exists(invoice_path):
                os.unlink(invoice_path)

    def test_appends_to_existing_invoices(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([{"id": 1}], f)
            invoice_path = f.name

        try:
            repo = FileInvoiceRepository(invoice_path)
            repo.save_invoice({"id": 2})

            invoices = repo.get_all_invoices()
            assert len(invoices) == 2
            assert invoices[0]["id"] == 1
            assert invoices[1]["id"] == 2
        finally:
            os.unlink(invoice_path)

    def test_returns_empty_list_when_file_missing(self):
        repo = FileInvoiceRepository("/nonexistent/path.json")
        assert repo.get_all_invoices() == []


class TestInMemoryConfigRepository:
    def test_returns_configured_plan_prices(self):
        prices = {"basic": Decimal("10"), "pro": Decimal("25")}
        repo = InMemoryConfigRepository(prices)

        result = repo.get_plan_prices()
        assert result == prices

    def test_returns_copy_not_reference(self):
        prices = {"basic": Decimal("10")}
        repo = InMemoryConfigRepository(prices)

        result = repo.get_plan_prices()
        result["basic"] = Decimal("999")

        assert repo.get_plan_prices()["basic"] == Decimal("10")


class TestInMemoryInvoiceRepository:
    def test_saves_and_retrieves_invoices(self):
        repo = InMemoryInvoiceRepository()

        repo.save_invoice({"id": 1})
        repo.save_invoice({"id": 2})

        invoices = repo.get_all_invoices()
        assert len(invoices) == 2
        assert invoices[0]["id"] == 1
        assert invoices[1]["id"] == 2

    def test_starts_empty(self):
        repo = InMemoryInvoiceRepository()
        assert repo.get_all_invoices() == []

    def test_returns_copy_not_reference(self):
        repo = InMemoryInvoiceRepository()
        repo.save_invoice({"id": 1})

        invoices = repo.get_all_invoices()
        invoices.append({"id": 999})

        assert len(repo.get_all_invoices()) == 1
