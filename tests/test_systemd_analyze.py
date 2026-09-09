"""Pure parser tests. The single-stage container shape is real, captured
output (verified live before writing systemd_analyze.py, see its
docstring); the multi-stage/multi-token-duration shapes are the
well-documented systemd time-formatting format this test environment's
own container boot can't produce (no real firmware/kernel stage exists
inside a container), not a guess -- both are exercised here so the
parser is proven correct for both, and the real end-to-end wiring is
additionally covered in test_systemd_analyze_integration.py.
"""

from __future__ import annotations

import pytest

from baslangic_optimizasyon_araci.runner import RunnerError
from baslangic_optimizasyon_araci.systemd_analyze import (
    get_blame,
    get_boot_time_breakdown,
    parse_blame_output,
    parse_time_output,
)

_REAL_CONTAINER_TIME_OUTPUT = "Startup finished in 703ms (userspace) \ngraphical.target was never reached.\n"

_REAL_CONTAINER_BLAME_OUTPUT = (
    "165ms systemd-journald.service\n"
    " 61ms systemd-logind.service\n"
    " 61ms avahi-daemon.service\n"
    " 60ms systemd-journal-flush.service\n"
    " 14ms systemd-update-utmp.service\n"
)

_DOCUMENTED_MULTI_STAGE_TIME_OUTPUT = (
    "Startup finished in 1.234s (firmware) + 567ms (loader) + 890ms (kernel) "
    "+ 200ms (initrd) + 1.500s (userspace) = 4.391s\n"
)


def test_parse_time_output_real_container_shape_single_stage_no_total():
    breakdown = parse_time_output(_REAL_CONTAINER_TIME_OUTPUT)
    assert breakdown.userspace_ms == 703
    assert breakdown.firmware_ms is None
    assert breakdown.kernel_ms is None
    assert breakdown.total_ms == 703  # summed from the one stage present, no "=" in the real line


def test_parse_time_output_documented_multi_stage_shape_with_total():
    breakdown = parse_time_output(_DOCUMENTED_MULTI_STAGE_TIME_OUTPUT)
    assert breakdown.firmware_ms == 1234
    assert breakdown.loader_ms == 567
    assert breakdown.kernel_ms == 890
    assert breakdown.initrd_ms == 200
    assert breakdown.userspace_ms == 1500
    assert breakdown.total_ms == 4391  # from the real "= 4.391s" suffix, not a re-sum


def test_parse_time_output_empty_input():
    breakdown = parse_time_output("")
    assert breakdown.total_ms == 0
    assert breakdown.userspace_ms is None


def test_parse_blame_output_real_container_shape():
    entries = parse_blame_output(_REAL_CONTAINER_BLAME_OUTPUT)
    assert len(entries) == 5
    assert entries[0].unit == "systemd-journald.service"
    assert entries[0].time_ms == 165
    assert entries[2].unit == "avahi-daemon.service"
    assert entries[2].time_ms == 61


def test_parse_blame_output_strips_leading_padding():
    # " 61ms avahi-daemon.service" has real leading-space column padding.
    entries = parse_blame_output(" 61ms avahi-daemon.service\n")
    assert entries[0].time_ms == 61


def test_parse_blame_output_multi_token_duration():
    # Documented systemd format for anything over a minute -- a real,
    # well-known slow unit (see reference.py) is exactly the kind of
    # service that can actually take this long.
    entries = parse_blame_output("1min 30.500s NetworkManager-wait-online.service\n")
    assert entries[0].time_ms == 90500
    assert entries[0].unit == "NetworkManager-wait-online.service"


def test_parse_blame_output_skips_blank_lines():
    entries = parse_blame_output("165ms a.service\n\n 61ms b.service\n")
    assert len(entries) == 2


def test_parse_blame_output_empty_input():
    assert parse_blame_output("") == []


class _FakeRunner:
    def __init__(self, stdout="", stderr="", exit_code=0):
        self.stdout, self.stderr, self.exit_code = stdout, stderr, exit_code

    def run(self, args, *, timeout=60.0):
        from baslangic_optimizasyon_araci.runner import CommandResult

        return CommandResult(stdout=self.stdout, stderr=self.stderr, exit_code=self.exit_code)


def test_get_boot_time_breakdown_uses_real_command_and_parses():
    runner = _FakeRunner(stdout=_REAL_CONTAINER_TIME_OUTPUT, exit_code=0)
    breakdown = get_boot_time_breakdown(runner)
    assert breakdown.userspace_ms == 703


def test_get_boot_time_breakdown_raises_on_nonzero_exit():
    runner = _FakeRunner(stdout="", stderr="command not found", exit_code=127)
    with pytest.raises(RunnerError):
        get_boot_time_breakdown(runner)


def test_get_blame_uses_real_command_and_parses():
    runner = _FakeRunner(stdout=_REAL_CONTAINER_BLAME_OUTPUT, exit_code=0)
    entries = get_blame(runner)
    assert len(entries) == 5


def test_get_blame_raises_on_nonzero_exit():
    runner = _FakeRunner(stdout="", stderr="oops", exit_code=1)
    with pytest.raises(RunnerError):
        get_blame(runner)
