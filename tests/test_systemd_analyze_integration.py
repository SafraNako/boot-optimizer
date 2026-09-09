"""Real systemd-analyze calls against a real, disposable systemd-in-
Docker container -- no mocking anywhere in this file.
"""

from __future__ import annotations

from baslangic_optimizasyon_araci import systemd_analyze
from baslangic_optimizasyon_araci.advisor import build_suggestions
from baslangic_optimizasyon_araci.runner import DockerExecRunner

from conftest import requires_docker


@requires_docker
def test_get_boot_time_breakdown_against_real_container(boot_container):
    runner = DockerExecRunner(boot_container)
    breakdown = systemd_analyze.get_boot_time_breakdown(runner)
    assert breakdown.total_ms > 0
    # A real container boot never has a real firmware/kernel stage.
    assert breakdown.userspace_ms is not None


@requires_docker
def test_get_blame_against_real_container(boot_container):
    runner = DockerExecRunner(boot_container)
    blame = systemd_analyze.get_blame(runner)
    assert len(blame) > 0
    assert all(entry.time_ms >= 0 for entry in blame)
    # Real, actually-present units from this container's own boot.
    unit_names = {entry.unit for entry in blame}
    assert "avahi-daemon.service" in unit_names


@requires_docker
def test_avahi_daemon_is_genuinely_suggested_from_real_blame_data(boot_container):
    """The end-to-end proof this matters: avahi-daemon is really
    installed, really enabled, really took real boot time in this
    container -- and the advisor, given that real data, really flags it.
    """
    runner = DockerExecRunner(boot_container)
    blame = systemd_analyze.get_blame(runner)
    suggestions = build_suggestions(blame)
    suggested_units = {s.unit for s in suggestions}
    assert "avahi-daemon.service" in suggested_units
