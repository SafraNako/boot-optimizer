"""Real `systemd-analyze time`/`blame` parsing.

Verified live against a real systemd-in-Docker container before writing
this module: `systemd-analyze time` reports only the stages it can
actually measure -- inside a container, no real firmware/bootloader/
kernel boot happens, so all that's ever reported is a single
"(userspace)" stage and no "=" grand total (there's nothing to sum):

    Startup finished in 703ms (userspace)
    graphical.target was never reached.

On real hardware it reports more stages, "+"-joined, with a "=" grand
total, e.g. "Startup finished in 1.234s (firmware) + 567ms (loader) +
890ms (kernel) + 200ms (initrd) + 1.500s (userspace) = 4.391s" -- a
well-documented, stable systemd format this parser also handles, even
though this test environment's own boot can only produce the simpler,
single-stage shape live.

`systemd-analyze blame` output was also verified live -- lines are
right-padded with leading spaces for column alignment (e.g. " 61ms
avahi-daemon.service"), one real duration followed by a real unit name,
sorted slowest-first.
"""

from __future__ import annotations

import re

from .models import BlameEntry, BootTimeBreakdown
from .runner import RunnerError

# A run of one-or-more "<number><unit>" tokens, e.g. "703ms" or the
# multi-token "1min 2.345s" systemd produces for anything over a minute.
_DURATION_RE = r"(?:\d+(?:\.\d+)?(?:h|min|ms|us|s)\s*)+"
_UNIT_TOKEN_RE = re.compile(r"(\d+(?:\.\d+)?)(h|min|ms|us|s)")
_UNIT_TO_MS = {"h": 3_600_000.0, "min": 60_000.0, "s": 1000.0, "ms": 1.0, "us": 0.001}

_STAGE_PAIR_RE = re.compile(rf"({_DURATION_RE})\(([a-z]+)\)")
_TOTAL_RE = re.compile(rf"=\s*({_DURATION_RE})")
_BLAME_LINE_RE = re.compile(rf"^({_DURATION_RE})(\S+)$")


def _parse_duration_to_ms(text: str) -> int:
    total = 0.0
    for value, unit in _UNIT_TOKEN_RE.findall(text):
        total += float(value) * _UNIT_TO_MS[unit]
    return round(total)


def parse_time_output(text: str) -> BootTimeBreakdown:
    first_line = text.splitlines()[0] if text.strip() else ""

    stages: dict[str, int] = {}
    for duration_text, label in _STAGE_PAIR_RE.findall(first_line):
        stages[label] = _parse_duration_to_ms(duration_text)

    total_match = _TOTAL_RE.search(first_line)
    total_ms = _parse_duration_to_ms(total_match.group(1)) if total_match else sum(stages.values())

    return BootTimeBreakdown(
        firmware_ms=stages.get("firmware"), loader_ms=stages.get("loader"),
        kernel_ms=stages.get("kernel"), initrd_ms=stages.get("initrd"),
        userspace_ms=stages.get("userspace"), total_ms=total_ms,
    )


def parse_blame_output(text: str) -> list[BlameEntry]:
    entries = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        match = _BLAME_LINE_RE.match(line)
        if not match:
            continue  # a stray/unrecognized line -- skip rather than crash on it
        duration_text, unit = match.groups()
        entries.append(BlameEntry(unit=unit, time_ms=_parse_duration_to_ms(duration_text)))
    return entries


def get_boot_time_breakdown(runner) -> BootTimeBreakdown:
    result = runner.run(["systemd-analyze", "time"])
    if result.exit_code != 0:
        raise RunnerError(f"systemd-analyze time çalıştırılamadı: {result.stderr.strip()}")
    return parse_time_output(result.stdout)


def get_blame(runner) -> list[BlameEntry]:
    result = runner.run(["systemd-analyze", "blame"])
    if result.exit_code != 0:
        raise RunnerError(f"systemd-analyze blame çalıştırılamadı: {result.stderr.strip()}")
    return parse_blame_output(result.stdout)
