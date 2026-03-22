import os
import time
import subprocess
import socket
import requests
import pytest
from tests.utils import _normalize_state, SESSION, DEFAULT_HOST, DEFAULT_PORT

def _get_non_local_ip() -> str | None:
    """
    Пытаемся получить IP текущей машины в локальной сети.
    В случае ошибки -> None, делаем skip.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # строим маршрут к адресу
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip == '127.0.0.1':
            return None
        return ip
    except OSError:
        return None
    
    
def _pick_free_port(ip: str = '127.0.0.1') -> str:
    """Берём свободный TCP порт, чтобы не конфликтовать с другими процессами."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((ip, 0))
        port = s.getsockname()[1]
        return str(port)
    
    
def run_cli(exe_path: str, workdir: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [exe_path, *args],
        cwd=workdir,
        capture_output=True,
        text=True,
        check=False,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )


def wait_ok(base_url: str, timeout_s: float = 8.0) -> None:
    deadline = time.time() + timeout_s
    last_err = None
    last_status = None
    last_text = None
    
    while time.time() < deadline:
        try:
            r = SESSION.get(f"{base_url}/api/state", timeout=1.0)
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
        f"App did not become ready at {base_url}.\n"
        f"last_err={last_err}\n"
        f"last_status={last_status}\n"
        f"last_text={last_text}\n"
    )


def test_restart_keeps_host_port(app):
    # restart должен сохранить тот же host/port
    p = run_cli(app.exe_path, app.workdir, "restart")
    assert p.returncode == 0, f"restart failed:\n{p.stdout}\n{p.stderr}"

    wait_ok(app.base_url, timeout_s=10.0)


@pytest.mark.standalone
def test_can_start_with_defaults_and_stop():
    """
    Отдельный тест на дефолтные параметры.
    Важно: он стартует/стопает отдельный процесс, не тот что в session fixture.
    """
    # Определяем путь к exe
    exe_path = os.path.abspath("webcalculator.exe")
    # выделяем директорию из пути, если не получилось, берем текущую
    workdir = os.path.dirname(exe_path) or os.getcwd()

    # старт без аргументов => 127.0.0.1:17678
    p = run_cli(exe_path, workdir, "start")
    assert p.returncode == 0, f"start(default) failed:\n{p.stdout}\n{p.stderr}"

    base_url = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}"
    wait_ok(base_url, timeout_s=10.0)

    p2 = run_cli(exe_path, workdir, "stop")
    assert p2.returncode == 0, f"stop failed:\n{p2.stdout}\n{p2.stderr}"
    
    
@pytest.mark.standalone
def test_start_with_change_port_and_stop():
    """
    Отдельный тест на изменение порта
    """
    # Определяем путь к exe
    exe_path = os.path.abspath("webcalculator.exe")
    # выделяем директорию из пути, если не получилось, берем текущую
    workdir = os.path.dirname(exe_path) or os.getcwd()
    
    port = _pick_free_port()
    
    p = run_cli(exe_path, workdir, "start", DEFAULT_HOST, port)
    assert p.returncode == 0, f"start(default) failed:\n{p.stdout}\n{p.stderr}"

    base_url = f"http://{DEFAULT_HOST}:{port}"
    wait_ok(base_url, timeout_s=10.0)

    p2 = run_cli(exe_path, workdir, "stop")
    assert p2.returncode == 0, f"stop failed:\n{p2.stdout}\n{p2.stderr}"


@pytest.mark.standalone
def test_start_with_change_host_and_stop():
    """
    Отдельный тест на изменение адреса
    """
    # Определяем путь к exe
    exe_path = os.path.abspath("webcalculator.exe")
    # выделяем директорию из пути, если не получилось, берем текущую
    workdir = os.path.dirname(exe_path) or os.getcwd()
    
    host = _get_non_local_ip()
    
    if host is None:
        pytest.skip("No non-local IP detected")
        
    p = run_cli(exe_path, workdir, "start", host)
    assert p.returncode == 0, f"start(default) failed:\n{p.stdout}\n{p.stderr}"

    base_url = f"http://{host}:{DEFAULT_PORT}"
    wait_ok(base_url, timeout_s=10.0)

    p2 = run_cli(exe_path, workdir, "stop")
    assert p2.returncode == 0, f"stop failed:\n{p2.stdout}\n{p2.stderr}"


@pytest.mark.standalone
def test_start_with_change_host_port_and_stop():
    """
    Отдельный тест на изменение адреса и порта
    """
    # Определяем путь к exe
    exe_path = os.path.abspath("webcalculator.exe")
    # выделяем директорию из пути, если не получилось, берем текущую
    workdir = os.path.dirname(exe_path) or os.getcwd()
    
    host = _get_non_local_ip()
    
    if host is None:
        pytest.skip("No non-local IP detected")
    
    port = _pick_free_port(host)
    
    p = run_cli(exe_path, workdir, "start", host, port)
    assert p.returncode == 0, f"start(default) failed:\n{p.stdout}\n{p.stderr}"

    base_url = f"http://{host}:{port}"
    wait_ok(base_url, timeout_s=10.0)

    p2 = run_cli(exe_path, workdir, "stop")
    assert p2.returncode == 0, f"stop failed:\n{p2.stdout}\n{p2.stderr}"
    
    
def wait_down(base_url: str, timeout=5.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            SESSION.get(f"{base_url}/api/state", timeout=0.5)
        except requests.RequestException:
            return True  # стало недоступно = то, что нужно
        time.sleep(0.1)
    return False


@pytest.mark.standalone
def test_app_is_down_after_stop():
    """
    Отдельный тест на остановку.
    """
    # Определяем путь к exe
    exe_path = os.path.abspath("webcalculator.exe")
    # выделяем директорию из пути, если не получилось, берем текущую
    workdir = os.path.dirname(exe_path) or os.getcwd()

    # старт без аргументов => 127.0.0.1:17678
    p = run_cli(exe_path, workdir, "start")
    assert p.returncode == 0, f"start(default) failed:\n{p.stdout}\n{p.stderr}"

    base_url = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}"
    wait_ok(base_url, timeout_s=10.0)

    p2 = run_cli(exe_path, workdir, "stop")
    assert p2.returncode == 0, f"stop failed:\n{p2.stdout}\n{p2.stderr}"

    # убеждаемся, что больше не отвечает
    assert wait_down(base_url, timeout=8.0), "App is still reachable after stop"