from __future__ import annotations

import sys

import pytest

from baslangic_optimizasyon_araci.runner import DockerExecRunner, LocalRunner, RunnerError

from conftest import requires_docker


@pytest.mark.skipif(sys.platform == "linux", reason="guard only fires on non-Linux")
def test_local_runner_refuses_non_linux():
    with pytest.raises(RunnerError):
        LocalRunner()


def test_local_runner_allow_non_linux_runs_real_commands():
    runner = LocalRunner(allow_non_linux=True)
    result = runner.run(["echo", "merhaba"])
    assert result.stdout.strip() == "merhaba"


def test_local_runner_raises_on_missing_command():
    runner = LocalRunner(allow_non_linux=True)
    with pytest.raises(RunnerError):
        runner.run(["kesinlikle-boyle-bir-komut-yok"])


@requires_docker
def test_docker_exec_runner_runs_real_command(boot_container):
    runner = DockerExecRunner(boot_container)
    result = runner.run(["echo", "gercek"])
    assert result.stdout.strip() == "gercek"
