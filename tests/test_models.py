from __future__ import annotations

from baslangic_optimizasyon_araci.models import BlameEntry, BootTimeBreakdown, OptimizationReport, Suggestion


def test_breakdown_to_dict_round_trips_fields():
    breakdown = BootTimeBreakdown(
        firmware_ms=None, loader_ms=None, kernel_ms=1234, initrd_ms=None, userspace_ms=2345, total_ms=3579,
    )
    data = breakdown.to_dict()
    assert data["kernel_ms"] == 1234
    assert data["firmware_ms"] is None
    assert data["total_ms"] == 3579


def test_suggestion_to_dict():
    suggestion = Suggestion(unit="avahi-daemon.service", time_ms=250, reason="test")
    assert suggestion.to_dict() == {"unit": "avahi-daemon.service", "time_ms": 250, "reason": "test"}


def test_optimization_report_has_suggestions_true():
    report = OptimizationReport(breakdown=None, suggestions=[Suggestion("a.service", 1, "x")])
    assert report.has_suggestions is True


def test_optimization_report_has_suggestions_false_when_empty():
    report = OptimizationReport(breakdown=None)
    assert report.has_suggestions is False


def test_blame_entry_fields():
    entry = BlameEntry(unit="cron.service", time_ms=42)
    assert entry.unit == "cron.service"
    assert entry.time_ms == 42
