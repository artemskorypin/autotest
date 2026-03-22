import os
import subprocess
import time
from dataclasses import dataclass
from collections.abc import Iterator
import pytest
from tests.utils import _normalize_state, SESSION, DEFAULT_HOST, DEFAULT_PORT


@dataclass(frozen=True)
class AppConfig:
    exe_path: str
    workdir: str
    host: str
    port: str

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


def _wait_until_ready(cfg: AppConfig, timeout_s: float = 20.0) -> None:
    deadline = time.time() + timeout_s
    last_status = None
    last_text = None
    last_err = None

    # проверяем поднялось ли приложение
    while time.time() < deadline:
        try:
            r = SESSION.get(f"{cfg.base_url}/api/state", timeout=1.0)
            last_status = r.status_code
            last_text = (r.text or "")

            if last_status == 200:
                data = r.json()
                if isinstance(data, dict) and data.get("statusCode") == 0 and _normalize_state(data.get("state")) == "OK":
                    return
        except Exception as e:
            last_err = e

        time.sleep(0.2)

    raise RuntimeError(
        f"App did not become ready at {cfg.base_url}.\n"
        f"last_err={last_err}\n"
        f"last_status={last_status}\n"
        f"last_text={last_text}\n"
    )


def _run_cli(exe_path: str, workdir: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [exe_path, *args],
        cwd=workdir,
        capture_output=True,
        text=True,
        check=False,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )


@pytest.fixture(scope="session")
def app() -> Iterator[AppConfig]:
    """
    Поднимаем приложение перед всеми тестами и гасим после всех тестов.
    По ТЗ управление: start/stop/restart/show_log.
    """
    # Определяем путь к exe
    exe_path = os.path.abspath("webcalculator.exe")
    # выделяем директорию из пути, если не получилось, берем текущую
    workdir = os.path.dirname(exe_path) or os.getcwd()

    cfg = AppConfig(exe_path=exe_path, workdir=workdir, host=DEFAULT_HOST, port=DEFAULT_PORT)

    # start (defaults: 127.0.0.1:17678)
    p = _run_cli(cfg.exe_path, cfg.workdir, "start")

    if p.returncode != 0:
        raise RuntimeError(
            "Failed to start app.\n"
            f"returncode={p.returncode}\nstdout:\n{p.stdout}\nstderr:\n{p.stderr}"
        )
        
    try:
        _wait_until_ready(cfg, timeout_s=30.0)
        yield cfg
    finally:
        p2 = _run_cli(cfg.exe_path, cfg.workdir, "stop")
        if p2.returncode != 0:
            print(
                "WARNING: failed to stop app.\n"
                f"returncode={p2.returncode}\nstdout:\n{p2.stdout}\nstderr:\n{p2.stderr}"
            )