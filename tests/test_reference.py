from __future__ import annotations

from baslangic_optimizasyon_araci.reference import NON_ESSENTIAL_UNIT_NAMES, NON_ESSENTIAL_UNITS, reason_for


def test_every_entry_has_a_nonempty_unit_and_reason():
    for entry in NON_ESSENTIAL_UNITS:
        assert entry.unit.endswith(".service")
        assert len(entry.reason) > 10


def test_unit_names_are_unique():
    names = [entry.unit for entry in NON_ESSENTIAL_UNITS]
    assert len(names) == len(set(names))


def test_non_essential_unit_names_matches_the_list():
    assert NON_ESSENTIAL_UNIT_NAMES == {entry.unit for entry in NON_ESSENTIAL_UNITS}


def test_reason_for_known_unit():
    assert reason_for("bluetooth.service") is not None


def test_reason_for_unknown_unit_returns_none():
    assert reason_for("kesinlikle-boyle-bir-servis-yok.service") is None
