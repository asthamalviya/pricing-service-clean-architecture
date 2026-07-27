"""
Unit tests for Clock interface.

Testing technique: White-box unit testing of individual components.
"""

from datetime import date
from v1.clock import SystemClock, FixedClock


def test_system_clock_returns_current_date():
    clock = SystemClock()
    result = clock.today()
    assert isinstance(result, date)
    assert result == date.today()


def test_fixed_clock_returns_configured_date():
    fixed = date(2026, 7, 15)
    clock = FixedClock(fixed)

    assert clock.today() == fixed
    assert clock.today() == fixed


def test_fixed_clock_makes_prorata_deterministic():
    clock = FixedClock(date(2026, 7, 15))

    for _ in range(100):
        assert clock.today() == date(2026, 7, 15)
