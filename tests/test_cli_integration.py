"""Real CLI-level end-to-end tests against a real systemd container."""

from __future__ import annotations

import io

from baslangic_optimizasyon_araci.cli import build_parser, run

from conftest import requires_docker


def _run(argv):
    out = io.StringIO()
    parser = build_parser()
    args = parser.parse_args(argv)
    code = run(args, out=out)
    return code, out.getvalue()


@requires_docker
def test_analiz_against_real_container(boot_container):
    code, output = _run(["analiz", "--konteyner", boot_container])
    assert code == 0
    assert "Toplam açılış" in output


@requires_docker
def test_suclu_bul_against_real_container(boot_container):
    code, output = _run(["suclu-bul", "--konteyner", boot_container, "--limit", "5"])
    assert code == 0
    assert "service" in output


@requires_docker
def test_oneri_against_real_container_flags_avahi(boot_container):
    code, output = _run(["oneri", "--konteyner", boot_container])
    assert code == 0
    assert "avahi-daemon.service" in output


@requires_docker
def test_hepsi_against_real_container_combines_all_sections(boot_container):
    code, output = _run(["hepsi", "--konteyner", boot_container])
    assert code == 0
    assert "Toplam açılış" in output
    assert "avahi-daemon.service" in output


@requires_docker
def test_devre_disi_birak_really_disables_a_real_unit(boot_container):
    import subprocess

    before = subprocess.run(
        ["docker", "exec", boot_container, "systemctl", "is-enabled", "avahi-daemon.service"],
        capture_output=True, text=True,
    )
    assert before.stdout.strip() == "enabled"

    code, output = _run(["devre-disi-birak", "avahi-daemon.service", "--konteyner", boot_container])
    assert code == 0
    assert "devre dışı bırakıldı" in output

    after = subprocess.run(
        ["docker", "exec", boot_container, "systemctl", "is-enabled", "avahi-daemon.service"],
        capture_output=True, text=True,
    )
    assert after.stdout.strip() == "disabled"

    # Leave it re-enabled so other tests in this session-scoped container
    # (which run in an unspecified order) still see it as a genuinely
    # enabled, suggestible unit.
    subprocess.run(["docker", "exec", boot_container, "systemctl", "enable", "avahi-daemon.service"])
