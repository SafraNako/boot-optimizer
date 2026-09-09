from __future__ import annotations

from baslangic_optimizasyon_araci.advisor import build_suggestions
from baslangic_optimizasyon_araci.models import BlameEntry


def test_reference_listed_unit_over_threshold_is_suggested():
    blame = [BlameEntry(unit="avahi-daemon.service", time_ms=250)]
    suggestions = build_suggestions(blame)
    assert len(suggestions) == 1
    assert suggestions[0].unit == "avahi-daemon.service"
    assert suggestions[0].reason  # a real, non-empty reason is attached


def test_unlisted_unit_is_never_suggested_regardless_of_time():
    blame = [BlameEntry(unit="cron.service", time_ms=5000)]
    assert build_suggestions(blame) == []


def test_reference_listed_unit_under_threshold_is_not_suggested():
    blame = [BlameEntry(unit="bluetooth.service", time_ms=1)]
    assert build_suggestions(blame) == []


def test_suggestions_sorted_by_time_descending():
    blame = [
        BlameEntry(unit="avahi-daemon.service", time_ms=100),
        BlameEntry(unit="bluetooth.service", time_ms=900),
        BlameEntry(unit="cups.service", time_ms=500),
    ]
    suggestions = build_suggestions(blame)
    assert [s.unit for s in suggestions] == ["bluetooth.service", "cups.service", "avahi-daemon.service"]


def test_empty_blame_produces_no_suggestions():
    assert build_suggestions([]) == []


def test_mixed_essential_and_non_essential_units_only_flags_non_essential():
    blame = [
        BlameEntry(unit="cron.service", time_ms=9000),
        BlameEntry(unit="ModemManager.service", time_ms=300),
        BlameEntry(unit="dbus.service", time_ms=200),
    ]
    suggestions = build_suggestions(blame)
    assert [s.unit for s in suggestions] == ["ModemManager.service"]
