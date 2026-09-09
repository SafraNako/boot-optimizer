"""Human-readable (Turkish) CLI formatting -- pure functions, no I/O."""

from __future__ import annotations

from .models import BlameEntry, BootTimeBreakdown, OptimizationReport, Suggestion


def _fmt_ms(ms: int) -> str:
    if ms >= 1000:
        return f"{ms / 1000:.3f}s"
    return f"{ms}ms"


def format_breakdown(breakdown: BootTimeBreakdown) -> str:
    parts = []
    for label, value in (
        ("firmware", breakdown.firmware_ms), ("yükleyici", breakdown.loader_ms),
        ("çekirdek", breakdown.kernel_ms), ("initrd", breakdown.initrd_ms),
        ("kullanıcı alanı", breakdown.userspace_ms),
    ):
        if value is not None:
            parts.append(f"{label}: {_fmt_ms(value)}")
    detail = ", ".join(parts) if parts else "ayrıntı yok"
    return f"Toplam açılış süresi: {_fmt_ms(breakdown.total_ms)} ({detail})\n"


def format_blame(entries: list[BlameEntry], *, limit: int | None = None) -> str:
    if not entries:
        return "Hiç blame verisi yok.\n"
    shown = entries[:limit] if limit else entries
    lines = [f"  {_fmt_ms(e.time_ms):>10}  {e.unit}" for e in shown]
    return "\n".join(lines) + "\n"


def format_suggestions(suggestions: list[Suggestion]) -> str:
    if not suggestions:
        return "Kapsamdaki referans listesine göre öneri yok.\n"
    lines = [f"{len(suggestions)} öneri (referans listesindeki, gerçekten zaman alan servisler):"]
    for s in suggestions:
        lines.append(f"  [{_fmt_ms(s.time_ms)}] {s.unit}\n      neden: {s.reason}")
    return "\n".join(lines) + "\n"


def format_report(report: OptimizationReport) -> str:
    parts = []
    if report.breakdown is not None:
        parts.append(format_breakdown(report.breakdown))
    parts.append(format_blame(report.blame, limit=10))
    parts.append(format_suggestions(report.suggestions))
    return "\n".join(parts)
