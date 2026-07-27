"""
Repository pattern for config loading and invoice persistence.

Abstracts data access behind interfaces so the service layer doesn't
depend on file I/O. Enables fast, isolated testing with in-memory implementations.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List
import json
import os


class ConfigRepository(ABC):
    @abstractmethod
    def get_plan_prices(self) -> Dict[str, Decimal]:
        pass


class InvoiceRepository(ABC):
    @abstractmethod
    def save_invoice(self, invoice: dict) -> None:
        pass

    @abstractmethod
    def get_all_invoices(self) -> List[dict]:
        pass


class FileConfigRepository(ConfigRepository):
    def __init__(self, config_path: str):
        self._config_path = config_path

    def get_plan_prices(self) -> Dict[str, Decimal]:
        with open(self._config_path) as f:
            config = json.load(f)
        return {plan: Decimal(str(price)) for plan, price in config.items()}


class FileInvoiceRepository(InvoiceRepository):
    def __init__(self, invoice_path: str):
        self._invoice_path = invoice_path

    def save_invoice(self, invoice: dict) -> None:
        records = self.get_all_invoices()
        records.append(invoice)
        with open(self._invoice_path, "w") as f:
            json.dump(records, f, indent=2, default=str)

    def get_all_invoices(self) -> List[dict]:
        if not os.path.exists(self._invoice_path):
            return []
        with open(self._invoice_path) as f:
            return json.load(f)


class InMemoryConfigRepository(ConfigRepository):
    def __init__(self, plan_prices: Dict[str, Decimal]):
        self._plan_prices = plan_prices

    def get_plan_prices(self) -> Dict[str, Decimal]:
        return self._plan_prices.copy()


class InMemoryInvoiceRepository(InvoiceRepository):
    def __init__(self):
        self._invoices: List[dict] = []

    def save_invoice(self, invoice: dict) -> None:
        self._invoices.append(invoice)

    def get_all_invoices(self) -> List[dict]:
        return self._invoices.copy()
