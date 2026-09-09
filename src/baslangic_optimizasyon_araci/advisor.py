"""Pure logic: given real, already-parsed blame data, decide what to
suggest. No I/O here -- kept separate from systemd_analyze.py so this
can be tested exhaustively without a container, exactly like disk-
recovery-tool's carver/verify split.
"""

from __future__ import annotations

from .models import BlameEntry, Suggestion
from .reference import NON_ESSENTIAL_UNIT_NAMES, reason_for

# Below this, a unit's real contribution to boot time is small enough
# that disabling it wouldn't meaningfully help -- so it's left out of
# suggestions even if it's on the reference list, to keep the report
# focused on what's actually worth acting on.
_MIN_WORTH_SUGGESTING_MS = 50


def build_suggestions(blame: list[BlameEntry]) -> list[Suggestion]:
    suggestions = []
    for entry in blame:
        if entry.unit not in NON_ESSENTIAL_UNIT_NAMES:
            continue
        if entry.time_ms < _MIN_WORTH_SUGGESTING_MS:
            continue
        suggestions.append(Suggestion(unit=entry.unit, time_ms=entry.time_ms, reason=reason_for(entry.unit)))
    # Biggest real time cost first -- that's what an operator should
    # look at first for the most actual benefit.
    suggestions.sort(key=lambda s: s.time_ms, reverse=True)
    return suggestions
