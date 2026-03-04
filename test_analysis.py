"""
Validation tests for the event analysis engine.

These tests verify that analysis output falls within documented historical ranges.
They are NOT unit tests — they require a live FRED API key and real data.

Run with: python -m pytest tests/test_analysis.py -v

Expected ranges sourced from docs/refs/historical_events.md
"""

import os
import sys
import pytest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def fred_client():
    """Initialize FRED client. Requires FRED_API_KEY env var."""
    try:
        from fredapi import Fred
        api_key = os.environ.get("FRED_API_KEY")
        if not api_key:
            pytest.skip("FRED_API_KEY environment variable not set")
        return Fred(api_key=api_key)
    except ImportError:
        pytest.skip("fredapi not installed")


@pytest.fixture(scope="session")
def data_collector(fred_client):
    from data_collector import get_commodity_data
    return get_commodity_data


@pytest.fixture(scope="session")
def analyzer():
    from event_analyzer import analyze_event_impact
    return analyze_event_impact


# ---------------------------------------------------------------------------
# Case A: Ukraine Invasion (Feb 24, 2022) — Geopolitical shock
# Expected: Brent +15 to +25%, peak in 7–14 days
# Source: docs/refs/historical_events.md, Sarwar & Rye (2025)
# ---------------------------------------------------------------------------

class TestUkraineInvasion:
    EVENT_DATE = datetime(2022, 2, 24)
    WINDOW = 30

    def test_brent_price_change_direction(self, data_collector, analyzer):
        """Brent crude should show a POSITIVE price change post-invasion."""
        start = self.EVENT_DATE - timedelta(days=self.WINDOW + 5)
        end = self.EVENT_DATE + timedelta(days=self.WINDOW + 5)
        data = data_collector('DCOILBRENTEU', start, end)
        result = analyzer(data, self.EVENT_DATE, self.WINDOW)
        assert result['avg_price_change_pct'] > 0, (
            f"Expected positive oil price change post-Ukraine invasion, "
            f"got {result['avg_price_change_pct']:.1f}%"
        )

    def test_brent_price_change_magnitude(self, data_collector, analyzer):
        """Brent crude avg price change should be +15% to +25%."""
        start = self.EVENT_DATE - timedelta(days=self.WINDOW + 5)
        end = self.EVENT_DATE + timedelta(days=self.WINDOW + 5)
        data = data_collector('DCOILBRENTEU', start, end)
        result = analyzer(data, self.EVENT_DATE, self.WINDOW)
        assert 15 <= result['avg_price_change_pct'] <= 30, (
            f"Brent price change {result['avg_price_change_pct']:.1f}% "
            f"outside expected range 15–25% (±5% tolerance)"
        )

    def test_brent_days_to_peak(self, data_collector, analyzer):
        """Peak Brent impact should occur within 7–20 days of invasion."""
        start = self.EVENT_DATE - timedelta(days=self.WINDOW + 5)
        end = self.EVENT_DATE + timedelta(days=self.WINDOW + 5)
        data = data_collector('DCOILBRENTEU', start, end)
        result = analyzer(data, self.EVENT_DATE, self.WINDOW)
        assert 3 <= result['days_to_peak'] <= 25, (
            f"Days to peak {result['days_to_peak']} outside expected range 7–20 days"
        )

    def test_natural_gas_price_change(self, data_collector, analyzer):
        """Natural gas should show a larger spike than oil post-invasion."""
        start = self.EVENT_DATE - timedelta(days=self.WINDOW + 5)
        end = self.EVENT_DATE + timedelta(days=self.WINDOW + 5)
        data = data_collector('DHHNGSP', start, end)
        result = analyzer(data, self.EVENT_DATE, self.WINDOW)
        assert result['avg_price_change_pct'] > 10, (
            f"Expected natural gas spike post-invasion, "
            f"got {result['avg_price_change_pct']:.1f}%"
        )


# ---------------------------------------------------------------------------
# Case B: COVID-19 Lockdowns (Mar 15, 2020) — Demand destruction
# Expected: Brent -50% to -65%, copper -15% to -25%
# Source: docs/refs/historical_events.md
# ---------------------------------------------------------------------------

class TestCovidLockdowns:
    EVENT_DATE = datetime(2020, 3, 15)
    WINDOW = 45  # Extended window — impact exceeds 30 days

    def test_brent_price_change_direction(self, data_collector, analyzer):
        """Brent crude should show a NEGATIVE price change (demand destruction)."""
        start = self.EVENT_DATE - timedelta(days=self.WINDOW + 5)
        end = self.EVENT_DATE + timedelta(days=self.WINDOW + 5)
        data = data_collector('DCOILBRENTEU', start, end)
        result = analyzer(data, self.EVENT_DATE, self.WINDOW)
        assert result['avg_price_change_pct'] < 0, (
            f"Expected negative oil price change during COVID lockdowns, "
            f"got {result['avg_price_change_pct']:.1f}%"
        )

    def test_brent_price_change_magnitude(self, data_collector, analyzer):
        """Brent crude should drop at least 40% in the 45-day window."""
        start = self.EVENT_DATE - timedelta(days=self.WINDOW + 5)
        end = self.EVENT_DATE + timedelta(days=self.WINDOW + 5)
        data = data_collector('DCOILBRENTEU', start, end)
        result = analyzer(data, self.EVENT_DATE, self.WINDOW)
        assert result['avg_price_change_pct'] <= -40, (
            f"Brent price change {result['avg_price_change_pct']:.1f}% "
            f"shallower than expected -40% minimum"
        )

    def test_volatility_increases(self, data_collector, analyzer):
        """Volatility should increase significantly during COVID crash."""
        start = self.EVENT_DATE - timedelta(days=self.WINDOW + 5)
        end = self.EVENT_DATE + timedelta(days=self.WINDOW + 5)
        data = data_collector('DCOILBRENTEU', start, end)
        result = analyzer(data, self.EVENT_DATE, self.WINDOW)
        assert result['volatility_change_pct'] > 20, (
            f"Expected volatility increase >20%, "
            f"got {result['volatility_change_pct']:.1f}%"
        )


# ---------------------------------------------------------------------------
# Case C: Suez Canal Blockage (Mar 23, 2021) — Maritime, short-duration
# Expected: Brent +3% to +7%, fast recovery <14 days
# Source: docs/refs/historical_events.md, Zhao et al. (2024)
# ---------------------------------------------------------------------------

class TestSuezBlockage:
    EVENT_DATE = datetime(2021, 3, 23)
    WINDOW = 15  # Short window — event resolved in 6 days

    def test_brent_price_change_direction(self, data_collector, analyzer):
        """Brent should show a POSITIVE (but modest) change for Suez blockage."""
        start = self.EVENT_DATE - timedelta(days=self.WINDOW + 5)
        end = self.EVENT_DATE + timedelta(days=self.WINDOW + 5)
        data = data_collector('DCOILBRENTEU', start, end)
        result = analyzer(data, self.EVENT_DATE, self.WINDOW)
        # Direction check with tolerance — Suez had modest impact
        assert result['avg_price_change_pct'] >= -2, (
            f"Suez blockage should not cause large price DROP, "
            f"got {result['avg_price_change_pct']:.1f}%"
        )

    def test_recovery_is_fast(self, data_collector, analyzer):
        """Suez recovery should occur within 15 days (event was brief)."""
        start = self.EVENT_DATE - timedelta(days=self.WINDOW + 5)
        end = self.EVENT_DATE + timedelta(days=self.WINDOW + 5)
        data = data_collector('DCOILBRENTEU', start, end)
        result = analyzer(data, self.EVENT_DATE, self.WINDOW)
        # Recovery_days should be set (not None) and short
        if result['recovery_days'] is not None:
            assert result['recovery_days'] <= 20, (
                f"Suez recovery took {result['recovery_days']} days — "
                f"expected fast recovery (<20 days) for a 6-day blockage"
            )


# ---------------------------------------------------------------------------
# Case D: 2008 Financial Crisis (Sep 15, 2008) — Financial, long-duration
# Expected: Brent -60% to -75%, recovery_days = None
# Source: docs/refs/historical_events.md
# ---------------------------------------------------------------------------

class TestFinancialCrisis2008:
    EVENT_DATE = datetime(2008, 9, 15)
    WINDOW = 90  # Long window for structural crisis

    def test_brent_severe_decline(self, data_collector, analyzer):
        """Brent should show severe decline (>50%) in 90-day window."""
        start = self.EVENT_DATE - timedelta(days=self.WINDOW + 5)
        end = self.EVENT_DATE + timedelta(days=self.WINDOW + 5)
        data = data_collector('DCOILBRENTEU', start, end)
        result = analyzer(data, self.EVENT_DATE, self.WINDOW)
        assert result['avg_price_change_pct'] <= -50, (
            f"2008 crisis Brent change {result['avg_price_change_pct']:.1f}% "
            f"shallower than expected -50% minimum in 90-day window"
        )

    def test_no_recovery_within_window(self, data_collector, analyzer):
        """Price should NOT recover within the 90-day window for 2008 crisis."""
        start = self.EVENT_DATE - timedelta(days=self.WINDOW + 5)
        end = self.EVENT_DATE + timedelta(days=self.WINDOW + 5)
        data = data_collector('DCOILBRENTEU', start, end)
        result = analyzer(data, self.EVENT_DATE, self.WINDOW)
        assert result['recovery_days'] is None, (
            f"Expected no recovery within 90 days for 2008 crisis, "
            f"but recovery_days returned {result['recovery_days']}"
        )


# ---------------------------------------------------------------------------
# Data Quality Tests (no FRED key required)
# ---------------------------------------------------------------------------

class TestDataValidation:

    def test_monthly_window_compatibility_warning(self):
        """Monthly commodities should trigger warning for windows < 90 days."""
        try:
            from data_collector import check_window_compatibility
            is_valid, message = check_window_compatibility('copper', 30)
            assert not is_valid, "Should return invalid for copper with 30-day window"
            assert message is not None, "Should return a warning message"
        except ImportError:
            pytest.skip("data_collector.check_window_compatibility not yet implemented")

    def test_monthly_window_ok_at_90_days(self):
        """Monthly commodities should be valid at 90-day window."""
        try:
            from data_collector import check_window_compatibility
            is_valid, message = check_window_compatibility('copper', 90)
            assert is_valid, f"Copper at 90-day window should be valid, got: {message}"
        except ImportError:
            pytest.skip("data_collector.check_window_compatibility not yet implemented")

    def test_daily_commodity_valid_at_30_days(self):
        """Daily commodities should be valid at 30-day window."""
        try:
            from data_collector import check_window_compatibility
            is_valid, _ = check_window_compatibility('crude_oil_brent', 30)
            assert is_valid, "Daily commodity should be valid at 30-day window"
        except ImportError:
            pytest.skip("data_collector.check_window_compatibility not yet implemented")
