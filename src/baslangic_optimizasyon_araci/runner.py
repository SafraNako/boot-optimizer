"""Command runners: abstract *where* systemd-analyze/systemctl get
invoked -- the same LocalRunner/DockerExecRunner pattern used across
this whole project series.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass


class RunnerError(RuntimeError):
    pass


@dataclass
class CommandResult:
    stdout: str
    stderr: str
    exit_code: int


class LocalRunner:
    def __init__(self, *, allow_non_linux: bool = False) -> None:
        if not allow_non_linux and sys.platform != "linux":
            raise RunnerError(
                "Yerel uygulama yalnızca Linux üzerinde çalışır "
                f"(bu makine: {sys.platform}). Bir Linux hedefi için --konteyner kullan."
            )

    def run(self, args: list[str], *, timeout: float = 60.0) -> CommandResult:
        try:
            proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        except FileNotFoundError as exc:
            raise RunnerError(f"komut bulunamadı: {args[0]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise RunnerError(f"zaman aşımı: {' '.join(args)}") from exc
        return CommandResult(stdout=proc.stdout, stderr=proc.stderr, exit_code=proc.returncode)


class DockerExecRunner:
    def __init__(self, container: str, *, docker_binary: str = "docker") -> None:
        self.container = container
        self.docker_binary = docker_binary

    def run(self, args: list[str], *, timeout: float = 60.0) -> CommandResult:
        full = [self.docker_binary, "exec", self.container, *args]
        try:
            proc = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
        except FileNotFoundError as exc:
            raise RunnerError("docker komutu bulunamadı") from exc
        except subprocess.TimeoutExpired as exc:
            raise RunnerError(f"zaman aşımı: {' '.join(args)}") from exc
        return CommandResult(stdout=proc.stdout, stderr=proc.stderr, exit_code=proc.returncode)
