# boot-optimizer

Parses real `systemd-analyze time`/`blame` output on a Linux target
(local machine or a Docker container), shows what actually took time
during boot, and cross-references it against a small, curated list of
commonly-non-essential units to suggest — never auto-apply in bulk —
what might be worth disabling.

CLI and internal package names are in Turkish
(`baslangic-optimizasyon-araci` / `baslangic_optimizasyon_araci`),
consistent with the other tools in this project series; code and this
document are in English.

## What it does

- `analiz` (analyze): the real top-level boot-time breakdown
  (`systemd-analyze time`) — firmware/loader/kernel/initrd/userspace,
  whichever stages the target actually reports.
- `suclu-bul` (find-the-culprit): every unit's real activation time
  (`systemd-analyze blame`), slowest first.
- `oneri` (suggest): cross-references real blame data against
  [`reference.py`](src/baslangic_optimizasyon_araci/reference.py)'s
  curated list — read-only, prints suggestions with a real reason for
  each, changes nothing.
- `hepsi` (all): the three above, combined into one report.
- `devre-disi-birak <servis>` (disable): a real, explicit, single-unit
  `systemctl disable` — opt-in and one unit at a time, deliberately not
  a "disable everything the tool suggested" bulk action.

## What `systemd-analyze` actually looks like — verified before parsing

Both output formats were checked against a real, live systemd-in-Docker
container before `systemd_analyze.py` was written, not assumed:

```
$ systemd-analyze time
Startup finished in 703ms (userspace)
graphical.target was never reached.

$ systemd-analyze blame
165ms systemd-journald.service
 61ms systemd-logind.service
 61ms avahi-daemon.service
...
```

A container never has a real firmware/bootloader/kernel boot stage to
measure, so `time` reports only `(userspace)` and — since there's only
one stage — no trailing `= <total>` grand total at all. On real hardware
`systemd-analyze time` reports more stages, `+`-joined, with a real `=`
total (e.g. `... (firmware) + ... (loader) + ... (kernel) + ... = 4.391s`)
— a well-documented, stable systemd format the parser also handles, even
though this project's own container-based tests can never produce that
shape live. `blame` lines are right-padded with leading spaces for
column alignment, and — for a genuinely slow unit — can report a
multi-token duration like `1min 30.500s` rather than a single number;
both are handled by the same duration-token regex, and both shapes have
their own tests (`tests/test_systemd_analyze.py` documents which is real
captured output and which is the documented format for a shape this
environment can't produce).

## Why the reference list is small and each entry says *why*

[`reference.py`](src/baslangic_optimizasyon_araci/reference.py) is
deliberately not exhaustive and never claims a unit is universally
useless — `bluetooth.service` is exactly what a laptop needs and exactly
what a headless server doesn't. Every entry names the real
hardware/feature it serves, so a suggestion always reads as "disable
this *if* you don't need X", not a blanket verdict. `advisor.py` also
only surfaces a suggestion when the real, measured time is above a small
threshold (50ms) — a reference-listed unit that barely registered in
this particular boot isn't worth a line in the report.

`NetworkManager-wait-online.service` is on the list for a well-known,
real reason: it makes boot *wait* for full network readiness, which is a
frequently-cited real-world boot-time cost most systems don't actually
need to block on.

## Verifying the advisor against something real, not just parsed text

The integration suite installs `avahi-daemon` (a small, common mDNS
package) alongside systemd specifically so at least one reference-listed
unit is genuinely present, enabled, and contributes real boot time in
the test container —
`test_avahi_daemon_is_genuinely_suggested_from_real_blame_data` in
[`tests/test_systemd_analyze_integration.py`](tests/test_systemd_analyze_integration.py)
proves the full real pipeline (real `systemd-analyze blame` → real
parsing → the advisor's real matching logic) actually flags it, not that
the pieces work in isolation.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
baslangic-optimizasyon-araci hepsi --konteyner benim-konteynerim
baslangic-optimizasyon-araci suclu-bul --yerel --limit 20
baslangic-optimizasyon-araci oneri --konteyner benim-konteynerim
baslangic-optimizasyon-araci devre-disi-birak avahi-daemon.service --konteyner benim-konteynerim
```

## Scope and limitations

- Reads `systemd-analyze`/`systemctl` only — no support for other init
  systems, and no attempt to reduce boot time by any means other than
  disabling a whole unit (no service-internal tuning, no parallelism
  changes).
- `devre-disi-birak` is real and immediate (`systemctl disable`) but
  reversible with a plain `systemctl enable` — there's no separate
  "undo" command in this tool, since systemctl's own is already the
  right, standard tool for that.
- The reference list is short and curated, not a comprehensive database
  of every unit that could ever be safe to disable on every distro.

## Testing

Real tests throughout — no mocking of `systemd-analyze`/`systemctl` in
the integration suite:

- Pure unit tests for duration/output parsing (both real captured shapes
  and documented-but-unreproducible-here shapes), the advisor's matching
  and threshold logic, and report formatting.
- Integration tests against a real, disposable, systemd-enabled
  `debian:bookworm-slim` container (the same `docker commit` + systemd-
  as-PID-1 recipe established in `service-monitor`, #66): real
  `systemd-analyze time`/`blame`, a real advisor match against a really
  installed and enabled unit, and a real `devre-disi-birak` that
  genuinely flips `systemctl is-enabled` from `enabled` to `disabled`.

```bash
pytest -v
```

Docker-based tests are skipped automatically if Docker isn't available.

## License

MIT — see [LICENSE](LICENSE).
