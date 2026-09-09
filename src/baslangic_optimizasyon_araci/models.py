"""Data shapes shared across the package -- dataclasses, JSON-friendly,
same lightweight pattern as the rest of this project series.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BootTimeBreakdown:
    """The real, top-level breakdown `systemd-analyze time` reports.
    Fields are in milliseconds; a stage systemd-analyze didn't report at
    all (common in containers -- there's no real firmware/bootloader/
    kernel stage to time) stays None rather than being guessed at as 0.
    """

    firmware_ms: int | None
    loader_ms: int | None
    kernel_ms: int | None
    initrd_ms: int | None
    userspace_ms: int | None
    total_ms: int

    def to_dict(self) -> dict:
        return {
            "firmware_ms": self.firmware_ms, "loader_ms": self.loader_ms,
            "kernel_ms": self.kernel_ms, "initrd_ms": self.initrd_ms,
            "userspace_ms": self.userspace_ms, "total_ms": self.total_ms,
        }


@dataclass
class BlameEntry:
    """One line of real `systemd-analyze blame` output: how long one
    unit took to finish activating, in milliseconds.
    """

    unit: str
    time_ms: int


@dataclass
class Suggestion:
    unit: str
    time_ms: int
    reason: str

    def to_dict(self) -> dict:
        return {"unit": self.unit, "time_ms": self.time_ms, "reason": self.reason}


@dataclass
class OptimizationReport:
    breakdown: BootTimeBreakdown | None
    blame: list[BlameEntry] = field(default_factory=list)
    suggestions: list[Suggestion] = field(default_factory=list)

    @property
    def has_suggestions(self) -> bool:
        return len(self.suggestions) > 0
