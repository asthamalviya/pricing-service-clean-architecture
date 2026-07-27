"""
Clock interface for dependency injection of date/time.

Allows tests to provide deterministic dates for pro-rata calculations
instead of relying on datetime.now().
"""

from abc import ABC, abstractmethod
from datetime import date


class Clock(ABC):
    @abstractmethod
    def today(self) -> date:
        pass


class SystemClock(Clock):
    def today(self) -> date:
        return date.today()


class FixedClock(Clock):
    def __init__(self, fixed_date: date):
        self._date = fixed_date

    def today(self) -> date:
        return self._date
