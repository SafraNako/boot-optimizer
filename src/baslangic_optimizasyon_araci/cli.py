"""CLI: `baslangic-optimizasyon-araci <komut> ...`"""

from __future__ import annotations

import argparse
import sys
from typing import TextIO

from . import systemd_analyze
from .advisor import build_suggestions
from .models import OptimizationReport
from .report import format_blame, format_breakdown, format_report, format_suggestions
from .runner import DockerExecRunner, LocalRunner, RunnerError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="baslangic-optimizasyon-araci",
        description="Gerçek systemd-analyze verisine göre açılış süresini analiz eder, en çok zaman alan "
        "servisleri sıralar, ve küçük/küratörlü bir referans listesine göre kapatılabilecek servisleri önerir.",
    )

    def add_target_args(p: argparse.ArgumentParser) -> None:
        target = p.add_mutually_exclusive_group(required=True)
        target.add_argument("--yerel", action="store_true", help="Bu makinede çalıştır (yalnızca Linux).")
        target.add_argument("--konteyner", metavar="ISIM", help="Çalışan bir Docker konteynerinde çalıştır.")

    sub = parser.add_subparsers(dest="command", required=True)

    analiz = sub.add_parser("analiz", help="Toplam açılış süresi dökümünü göster.")
    add_target_args(analiz)

    sucluBul = sub.add_parser("suclu-bul", help="En çok zaman alan servisleri sırala (systemd-analyze blame).")
    sucluBul.add_argument("--limit", type=int, default=10)
    add_target_args(sucluBul)

    oneri = sub.add_parser("oneri", help="Referans listesine göre kapatılabilecek servisleri öner (salt-okunur).")
    add_target_args(oneri)

    hepsi = sub.add_parser("hepsi", help="Döküm + suclu-bul + oneri, tek raporda.")
    add_target_args(hepsi)

    devreDisi = sub.add_parser("devre-disi-birak", help="Tek bir servisi gerçekten devre dışı bırak (systemctl disable).")
    devreDisi.add_argument("servis")
    add_target_args(devreDisi)

    return parser


def _build_runner(args: argparse.Namespace):
    if args.yerel:
        return LocalRunner()
    return DockerExecRunner(args.konteyner)


def run(args: argparse.Namespace, *, out: TextIO | None = None) -> int:
    # `out` resolves here, not as a signature default -- a signature
    # default binds once at import time and would silently escape any
    # later redirection of sys.stdout (e.g. pytest's capsys), a bug found
    # and fixed in theme-manager's cli.py (#65).
    if out is None:
        out = sys.stdout

    try:
        runner = _build_runner(args)
    except RunnerError as exc:
        print(str(exc), file=out)
        return 1

    if args.command == "analiz":
        try:
            breakdown = systemd_analyze.get_boot_time_breakdown(runner)
        except RunnerError as exc:
            print(str(exc), file=out)
            return 1
        print(format_breakdown(breakdown), file=out, end="")
        return 0

    if args.command == "suclu-bul":
        try:
            blame = systemd_analyze.get_blame(runner)
        except RunnerError as exc:
            print(str(exc), file=out)
            return 1
        print(format_blame(blame, limit=args.limit), file=out, end="")
        return 0

    if args.command == "oneri":
        try:
            blame = systemd_analyze.get_blame(runner)
        except RunnerError as exc:
            print(str(exc), file=out)
            return 1
        suggestions = build_suggestions(blame)
        print(format_suggestions(suggestions), file=out, end="")
        return 0

    if args.command == "hepsi":
        try:
            breakdown = systemd_analyze.get_boot_time_breakdown(runner)
            blame = systemd_analyze.get_blame(runner)
        except RunnerError as exc:
            print(str(exc), file=out)
            return 1
        report = OptimizationReport(breakdown=breakdown, blame=blame, suggestions=build_suggestions(blame))
        print(format_report(report), file=out, end="")
        return 0

    if args.command == "devre-disi-birak":
        result = runner.run(["systemctl", "disable", args.servis])
        if result.exit_code != 0:
            print(f"{args.servis} devre dışı bırakılamadı: {result.stderr.strip()}", file=out)
            return 1
        print(f"{args.servis} devre dışı bırakıldı.", file=out)
        return 0

    print(f"bilinmeyen komut: {args.command}", file=out)  # pragma: no cover
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
