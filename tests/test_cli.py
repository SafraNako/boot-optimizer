from __future__ import annotations

import io

from baslangic_optimizasyon_araci.cli import build_parser, main, run


def _run(argv):
    out = io.StringIO()
    parser = build_parser()
    args = parser.parse_args(argv)
    code = run(args, out=out)
    return code, out.getvalue()


def test_parser_requires_exactly_one_target():
    parser = build_parser()
    try:
        parser.parse_args(["analiz"])
        assert False, "should have required --yerel or --konteyner"
    except SystemExit:
        pass


def test_yerel_on_non_linux_reports_error_without_touching_target():
    import sys

    if sys.platform == "linux":
        return
    code, output = _run(["analiz", "--yerel"])
    assert code == 1
    assert "yalnızca Linux" in output


def test_suclu_bul_default_limit():
    parser = build_parser()
    args = parser.parse_args(["suclu-bul", "--konteyner", "x"])
    assert args.limit == 10


def test_devre_disi_birak_requires_service_argument():
    parser = build_parser()
    try:
        parser.parse_args(["devre-disi-birak", "--konteyner", "x"])
        assert False, "should require a service name"
    except SystemExit:
        pass


def test_main_returns_int_exit_code_on_bad_target(capsys):
    import sys

    if sys.platform == "linux":
        return
    code = main(["analiz", "--yerel"])
    assert code == 1
    captured = capsys.readouterr()
    assert "yalnızca Linux" in captured.out
