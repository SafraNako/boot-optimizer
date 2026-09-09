"""A small, curated reference list of systemd units commonly safe to
disable for faster boot on a machine that doesn't need them -- NOT
exhaustive, and deliberately NOT a judgment about any specific machine
(a headless server has no use for Bluetooth; a laptop very much does).
Each entry names the real hardware/feature it serves and why it's a
common boot-time cost, so a suggestion is never just "disable this",
it's "disable this IF you don't need X".
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NonEssentialUnit:
    unit: str
    reason: str


# Sources: this is the same short list of "usually skippable on a
# server, or a desktop that doesn't need the feature" units that shows
# up repeatedly in real systemd boot-time tuning guides and
# `systemd-analyze blame` results in the wild.
NON_ESSENTIAL_UNITS: list[NonEssentialUnit] = [
    NonEssentialUnit("bluetooth.service", "Bluetooth donanımı yoksa ya da kullanılmıyorsa gereksiz."),
    NonEssentialUnit("cups.service", "Yazıcı kullanılmıyorsa (CUPS baskı servisi) gereksiz."),
    NonEssentialUnit("cups-browsed.service", "Ağdaki paylaşılan yazıcıları taramaz olur; CUPS kullanılmıyorsa gereksiz."),
    NonEssentialUnit("avahi-daemon.service", "mDNS/Bonjour ağ keşfi; yerel ağda .local isim çözümlemesi kullanılmıyorsa gereksiz."),
    NonEssentialUnit("ModemManager.service", "Mobil geniş bant (3G/4G) modem yoksa gereksiz."),
    NonEssentialUnit(
        "NetworkManager-wait-online.service",
        "Ağın tamamen hazır olmasını BEKLEYEREK açılışı geciktirir -- bilinen, sık rastlanan bir açılış yavaşlatıcısı; "
        "çoğu sistemin buna gerçekten ihtiyacı yoktur.",
    ),
    NonEssentialUnit("plymouth-quit-wait.service", "Grafik açılış ekranının (splash) bitmesini bekler; sunucularda anlamsız."),
    NonEssentialUnit("motd-news.service", "Açılışta uzaktan bir duyuru metni indirir; ağ gecikmesine bağımlı, gereksiz."),
    NonEssentialUnit("apt-news.service", "APT'nin açılışta uzaktan haber/duyuru çekmesi; gereksiz."),
    NonEssentialUnit("snapd.seeded.service", "Ubuntu snap paketlerinin ilk-açılış tohumlama işlemi; snap kullanılmıyorsa gereksiz."),
]

NON_ESSENTIAL_UNIT_NAMES = {entry.unit for entry in NON_ESSENTIAL_UNITS}


def reason_for(unit: str) -> str | None:
    for entry in NON_ESSENTIAL_UNITS:
        if entry.unit == unit:
            return entry.reason
    return None
