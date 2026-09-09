"""Shared test fixtures. Real, disposable, systemd-enabled container --
no mocking of systemctl/systemd-analyze anywhere in the integration
suite.

Getting a real systemd running as PID 1 inside Docker needs the same
recipe established in service-monitor (#66): `docker exec -d <container>
systemd` does NOT work (systemctl refuses with "System has not been
booted with systemd as init system (PID 1)" -- Docker only lets you set
a container's PID 1 at creation, not by exec'ing one in afterwards), so
this installs into a throwaway container first, `docker commit`s it to
an image, then runs a NEW container from that image with
`/lib/systemd/systemd` as the actual command -- plus `--privileged
--cgroupns=host` and a real (not read-only) `/sys/fs/cgroup` mount, both
also required or systemd never reaches "running".

`avahi-daemon` is installed alongside systemd specifically so at least
one real, reference-listed, boot-time-flaggable unit is genuinely
present and enabled -- proving the advisor's suggestions correspond to
something real, not just parsed text.

A real, found-not-guessed wrinkle: relying on avahi-daemon.service to
auto-start purely as a side effect of reaching multi-user.target turned
out not to be reliable across different real Docker+systemd
environments -- it auto-started and showed up in `systemd-analyze blame`
locally (against Colima), but never appeared in `blame` at all in CI
(GitHub Actions' runner), even though the unit was still genuinely
"enabled" there (a separate `systemctl is-enabled`/`disable` test passed
in the same CI run). `systemd-analyze blame` only ever lists a unit's
MOST RECENT activation -- verified live: stopping and manually
restarting avahi-daemon.service well after boot still updates its entry
in `blame` -- so the fix here doesn't chase why the CI runner's boot
ordering left it inactive; it makes the precondition genuinely true
before any test relies on it, by explicitly starting the unit and
confirming it's really active.
"""

from __future__ import annotations

import shutil
import subprocess
import time

import pytest

CONTAINER_NAME = "baslangic-testi"
IMAGE_NAME = "baslangic-testi-imaj"
PREP_CONTAINER_NAME = "baslangic-hazirlik"
BASE_IMAGE = "debian:bookworm-slim"
PACKAGES = ["systemd", "systemd-sysv", "avahi-daemon"]


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, timeout=10)
    except (subprocess.TimeoutExpired, OSError):
        return False
    return result.returncode == 0


DOCKER_AVAILABLE = _docker_available()

requires_docker = pytest.mark.skipif(
    not DOCKER_AVAILABLE, reason="Docker çalışmıyor -- konteyner tabanlı testler atlanıyor."
)


def _exec(container: str, *args: str, timeout: float = 60, check: bool = True):
    return subprocess.run(
        ["docker", "exec", container, *args],
        capture_output=True, text=True, timeout=timeout, check=check,
    )


@pytest.fixture(scope="session")
def boot_container():
    if not DOCKER_AVAILABLE:
        pytest.skip("Docker çalışmıyor -- konteyner tabanlı testler atlanıyor.")

    subprocess.run(["docker", "rm", "-f", PREP_CONTAINER_NAME, CONTAINER_NAME], capture_output=True)
    subprocess.run(["docker", "rmi", IMAGE_NAME], capture_output=True)

    try:
        subprocess.run(
            [
                "docker", "run", "-d", "--name", PREP_CONTAINER_NAME,
                "-e", "DEBIAN_FRONTEND=noninteractive",
                BASE_IMAGE, "sleep", "infinity",
            ],
            check=True, capture_output=True, timeout=60,
        )
        apt_opts = ["-o", "Acquire::Retries=5", "-o", "Acquire::http::Timeout=30"]
        _exec(PREP_CONTAINER_NAME, "apt-get", *apt_opts, "update", timeout=480)
        _exec(PREP_CONTAINER_NAME, "apt-get", *apt_opts, "install", "-y", "--no-install-recommends", *PACKAGES, timeout=480)
        subprocess.run(["docker", "commit", PREP_CONTAINER_NAME, IMAGE_NAME], check=True, capture_output=True, timeout=60)
        subprocess.run(["docker", "rm", "-f", PREP_CONTAINER_NAME], capture_output=True)

        subprocess.run(
            [
                "docker", "run", "-d", "--name", CONTAINER_NAME,
                "--privileged", "--cgroupns=host",
                "-v", "/sys/fs/cgroup:/sys/fs/cgroup:rw",
                IMAGE_NAME, "/lib/systemd/systemd", "--system", "--unit=multi-user.target",
            ],
            check=True, capture_output=True, timeout=60,
        )

        deadline = time.time() + 60
        last_state = ""
        while time.time() < deadline:
            probe = subprocess.run(
                ["docker", "exec", CONTAINER_NAME, "systemctl", "is-system-running"],
                capture_output=True, text=True, timeout=10,
            )
            last_state = probe.stdout.strip()
            if last_state in ("running", "degraded"):
                break
            time.sleep(2)
        else:
            pytest.skip(f"systemd konteyner içinde zamanında ayağa kalkmadı (son durum: {last_state!r}).")

        # Don't trust that avahi-daemon auto-started as a side effect of
        # boot ordering (see module docstring) -- make it genuinely true.
        subprocess.run(["docker", "exec", CONTAINER_NAME, "systemctl", "start", "avahi-daemon.service"], capture_output=True)
        active_deadline = time.time() + 30
        avahi_active = False
        while time.time() < active_deadline:
            probe = subprocess.run(
                ["docker", "exec", CONTAINER_NAME, "systemctl", "is-active", "avahi-daemon.service"],
                capture_output=True, text=True, timeout=10,
            )
            if probe.stdout.strip() == "active":
                avahi_active = True
                break
            time.sleep(1)
        if not avahi_active:
            pytest.skip("avahi-daemon.service konteyner içinde gerçekten etkinleştirilemedi.")

        yield CONTAINER_NAME
    finally:
        subprocess.run(["docker", "rm", "-f", PREP_CONTAINER_NAME, CONTAINER_NAME], capture_output=True)
        subprocess.run(["docker", "rmi", IMAGE_NAME], capture_output=True)
