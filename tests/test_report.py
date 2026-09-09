from __future__ import annotations

from baslangic_optimizasyon_araci.models import BlameEntry, BootTimeBreakdown, OptimizationReport, Suggestion
from baslangic_optimizasyon_araci.report import format_blame, format_breakdown, format_report, format_suggestions


def test_format_breakdown_shows_available_stages_only():
    breakdown = BootTimeBreakdown(
        firmware_ms=None, loader_ms=None, kernel_ms=1234, initrd_ms=None, userspace_ms=2345, total_ms=3579,
    )
    text = format_breakdown(breakdown)
    assert "çekirdek" in text
    assert "kullanıcı alanı" in text
    assert "firmware" not in text
    assert "3.579s" in text


def test_format_breakdown_sub_second_uses_ms():
    breakdown = BootTimeBreakdown(
        firmware_ms=None, loader_ms=None, kernel_ms=None, initrd_ms=None, userspace_ms=500, total_ms=500,
    )
    text = format_breakdown(breakdown)
    assert "500ms" in text


def test_format_blame_empty():
    assert "yok" in format_blame([])


def test_format_blame_respects_limit():
    entries = [BlameEntry(unit=f"u{i}.service", time_ms=i) for i in range(20)]
    text = format_blame(entries, limit=3)
    assert text.count(".service") == 3


def test_format_suggestions_empty():
    assert "yok" in format_suggestions([])


def test_format_suggestions_includes_reason():
    suggestions = [Suggestion(unit="bluetooth.service", time_ms=900, reason="test nedeni")]
    text = format_suggestions(suggestions)
    assert "bluetooth.service" in text
    assert "test nedeni" in text


def test_format_report_combines_all_sections():
    breakdown = BootTimeBreakdown(None, None, None, None, 1000, 1000)
    blame = [BlameEntry("a.service", 500)]
    suggestions = [Suggestion("bluetooth.service", 900, "test")]
    report = OptimizationReport(breakdown=breakdown, blame=blame, suggestions=suggestions)
    text = format_report(report)
    assert "Toplam açılış" in text
    assert "a.service" in text
    assert "bluetooth.service" in text


def test_format_report_without_breakdown():
    report = OptimizationReport(breakdown=None, blame=[BlameEntry("a.service", 1)])
    text = format_report(report)
    assert "Toplam açılış" not in text
    assert "a.service" in text
