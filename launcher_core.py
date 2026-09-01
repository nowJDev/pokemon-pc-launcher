# ADB와 scrcpy 제어에 필요한 장치 독립 핵심 로직을 제공한다.

from dataclasses import dataclass
import ipaddress
import json
import logging
import os
from pathlib import Path
import re
import socket
import subprocess
import threading
import time

from game_profiles import load_game_profiles


logging.getLogger(__name__).addHandler(logging.NullHandler())

DEFAULT_FPS = "제한 없음 (기본값)"
SUPPORTED_SCRCPY_VERSION = "4.1"
VIRTUAL_DISPLAY_MODE = "virtual_display"
MIRROR_MODE = "mirror"
RFC1918_NETWORKS = tuple(
    ipaddress.ip_network(network)
    for network in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
)


@dataclass(frozen=True)
class CommandResult:
    stdout: str
    stderr: str
    returncode: int
    timed_out: bool = False


@dataclass(frozen=True)
class AdbDevice:
    serial: str
    state: str
    details: str = ""

    @property
    def is_wireless(self):
        return ":" in self.serial


@dataclass(frozen=True)
class ScrcpyOptions:
    mode: str
    resolution: str
    fps: str = DEFAULT_FPS
    borderless: bool = False
    turn_screen_off: bool = False
    flex_display: bool = False


@dataclass(frozen=True)
class BinaryPaths:
    adb_path: str
    scrcpy_path: str
    missing: tuple[str, ...]


class WorkerRegistry:
    def __init__(self):
        self._lock = threading.Lock()
        self._workers = {}

    def start(self, name, target, *args, **kwargs):
        def run_target():
            try:
                target(*args, **kwargs)
            finally:
                with self._lock:
                    self._workers.pop(threading.current_thread(), None)

        thread = threading.Thread(target=run_target, name=name, daemon=True)
        with self._lock:
            self._workers[thread] = name
        thread.start()
        return thread

    def join_all(self, timeout):
        deadline = time.monotonic() + max(0, timeout)
        current = threading.current_thread()
        with self._lock:
            workers = [(thread, name) for thread, name in self._workers.items() if thread is not current]
        for thread, _ in workers:
            remaining = max(0, deadline - time.monotonic())
            thread.join(remaining)
        return sorted(name for thread, name in workers if thread.is_alive())


def _to_text(value):
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def run_command(args, timeout=5, logger=None):
    startupinfo = None
    if os.name == "nt" and hasattr(subprocess, "STARTUPINFO"):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

    try:
        completed = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            startupinfo=startupinfo,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            timeout=timeout,
        )
        return CommandResult(completed.stdout, completed.stderr, completed.returncode)
    except subprocess.TimeoutExpired as exc:
        message = f"명령이 {timeout}초 안에 끝나지 않았습니다."
        stderr = _to_text(exc.stderr)
        if stderr:
            message = f"{message} {stderr}"
        if logger:
            logger.warning("명령 timeout (%ss): %s", timeout, args[0])
        return CommandResult(_to_text(exc.stdout), message, -1, timed_out=True)
    except OSError as exc:
        if logger:
            logger.exception("명령 실행 실패: %s", args[0])
        return CommandResult("", str(exc), -1)


class CommandRunner:
    def __init__(self, logger=None):
        self.logger = logger

    def run(self, args, timeout=5):
        return run_command(args, timeout=timeout, logger=self.logger)


def parse_adb_devices(output):
    devices = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("List of devices attached") or line.startswith("*"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        devices.append(AdbDevice(parts[0], parts[1], " ".join(parts[2:])))
    return devices


def parse_package_list(output):
    packages = set()
    for line in output.splitlines():
        match = re.fullmatch(r"package:([^\s]+)", line.strip())
        if match:
            packages.add(match.group(1))
    return packages


def is_wifi_candidate_ip(value):
    try:
        address = ipaddress.ip_address(value.split("/", 1)[0].strip())
    except (AttributeError, ValueError):
        return False
    if not isinstance(address, ipaddress.IPv4Address):
        return False
    if address.is_loopback or address.is_link_local or address.is_multicast or address.is_unspecified:
        return False
    return any(address in network for network in RFC1918_NETWORKS)


def normalize_wireless_endpoint(value, default_port=5555):
    text = value.strip()
    if text.count(":") > 1:
        raise ValueError("IPv4 주소를 입력해 주세요.")
    if ":" in text:
        address, port_text = text.rsplit(":", 1)
        if not port_text.isdigit() or not 1 <= int(port_text) <= 65535:
            raise ValueError("포트 번호가 올바르지 않습니다.")
        port = int(port_text)
    else:
        address = text
        port = default_port
    if not is_wifi_candidate_ip(address):
        raise ValueError("사설 Wi-Fi IPv4 주소를 입력해 주세요.")
    return f"{address}:{port}"


def device_state_error(state):
    if state == "device":
        return None
    if state == "unauthorized":
        return "스마트폰에서 USB 디버깅 허용을 승인해 주세요."
    if state == "offline":
        return "ADB 기기가 offline 상태입니다. 연결을 다시 시도해 주세요."
    return f"ADB 기기가 정상 상태가 아닙니다: {state}"


def _cancel_requested(cancel_event):
    return cancel_event is not None and cancel_event.is_set()


def _append_ip_candidate(items, value, priority, order):
    address = value.split("/", 1)[0]
    if is_wifi_candidate_ip(address):
        items.append((priority, order, address))


def select_wifi_ip(route_output, addr_output, wifi_output):
    ranked = []
    order = 0

    for line in route_output.splitlines():
        source_match = re.search(r"\bsrc\s+(\d{1,3}(?:\.\d{1,3}){3})", line)
        if not source_match:
            continue
        interface_match = re.search(r"\bdev\s+(\S+)", line)
        interface = interface_match.group(1).lower() if interface_match else ""
        priority = 0 if interface.startswith(("wlan", "wifi")) else 2
        _append_ip_candidate(ranked, source_match.group(1), priority, order)
        order += 1

    current_interface = ""
    for line in addr_output.splitlines():
        interface_match = re.match(r"\d+:\s+([^:@]+)", line.strip())
        if interface_match:
            current_interface = interface_match.group(1).lower()
            continue
        address_match = re.search(r"\binet\s+(\d{1,3}(?:\.\d{1,3}){3})(?:/\d+)?", line)
        if address_match:
            priority = 1 if current_interface.startswith(("wlan", "wifi")) else 3
            _append_ip_candidate(ranked, address_match.group(1), priority, order)
            order += 1

    wifi_addresses = re.findall(r"\d{1,3}(?:\.\d{1,3}){3}", wifi_output)
    for address in wifi_addresses:
        _append_ip_candidate(ranked, address, 4, order)
        order += 1

    ranked.sort(key=lambda item: (item[0], item[1]))
    candidates = []
    for _, _, address in ranked:
        if address not in candidates:
            candidates.append(address)
    return (candidates[0] if candidates else None), candidates


def validate_resolution(value, orientation):
    match = re.fullmatch(r"(\d+)x(\d+)", value.strip().lower())
    if not match:
        raise ValueError("해상도는 가로x세로 형식이어야 합니다.")
    width, height = (int(part) for part in match.groups())
    if width < 320 or height < 320:
        raise ValueError("가로와 세로는 각각 최소 320이어야 합니다.")
    if width > 7680 or height > 7680:
        raise ValueError("가로와 세로는 각각 최대 7680이어야 합니다.")
    if orientation == "portrait" and width > height:
        return "현재 게임은 세로형 화면을 권장합니다."
    if orientation == "landscape" and height > width:
        return "현재 게임은 가로형 화면을 권장합니다."
    return None


def _default_config():
    profiles = load_game_profiles()
    return {
        "last_game": "pokemon_champions",
        "launch_mode": VIRTUAL_DISPLAY_MODE,
        "game_resolutions": {
            key: profile.default_resolution for key, profile in profiles.items()
        },
        "custom_resolution_enabled": {key: False for key in profiles},
        "custom_resolutions": {
            key: {
                "width": profile.default_resolution.split("x", 1)[0],
                "height": profile.default_resolution.split("x", 1)[1],
            }
            for key, profile in profiles.items()
        },
        "fps": DEFAULT_FPS,
        "borderless": False,
        "turn_screen_off": False,
        "flex_display": False,
        "kill_adb_server_on_exit": False,
        "wireless_ip": "192.168.0.16",
    }


def normalize_config(config):
    profiles = load_game_profiles()
    normalized = _default_config()
    if not isinstance(config, dict):
        return normalized

    game_key = config.get("last_game")
    if game_key in profiles:
        normalized["last_game"] = game_key

    mode = config.get("launch_mode")
    if mode in {VIRTUAL_DISPLAY_MODE, MIRROR_MODE}:
        normalized["launch_mode"] = mode

    incoming_resolutions = config.get("game_resolutions")
    if isinstance(incoming_resolutions, dict):
        for key, value in incoming_resolutions.items():
            if key in profiles and isinstance(value, str):
                try:
                    validate_resolution(value, profiles[key].orientation)
                except ValueError:
                    continue
                normalized["game_resolutions"][key] = value
    elif isinstance(config.get("resolution"), str):
        legacy_resolution = config["resolution"]
        try:
            validate_resolution(legacy_resolution, profiles["pokemon_champions"].orientation)
        except ValueError:
            pass
        else:
            normalized["game_resolutions"]["pokemon_champions"] = legacy_resolution

    incoming_enabled = config.get("custom_resolution_enabled")
    if isinstance(incoming_enabled, dict):
        for key, value in incoming_enabled.items():
            if key in profiles:
                normalized["custom_resolution_enabled"][key] = bool(value)
    elif isinstance(incoming_enabled, bool):
        normalized["custom_resolution_enabled"]["pokemon_champions"] = incoming_enabled

    incoming_custom = config.get("custom_resolutions")
    if isinstance(incoming_custom, dict):
        for key, value in incoming_custom.items():
            if key in profiles and isinstance(value, dict):
                width = str(value.get("width", ""))
                height = str(value.get("height", ""))
                try:
                    validate_resolution(f"{width}x{height}", profiles[key].orientation)
                except ValueError:
                    continue
                normalized["custom_resolutions"][key] = {"width": width, "height": height}
    elif "custom_width" in config or "custom_height" in config:
        width = str(config.get("custom_width", "1280"))
        height = str(config.get("custom_height", "720"))
        try:
            validate_resolution(f"{width}x{height}", profiles["pokemon_champions"].orientation)
        except ValueError:
            pass
        else:
            normalized["custom_resolutions"]["pokemon_champions"] = {
                "width": width,
                "height": height,
            }

    for key in (
        "borderless",
        "turn_screen_off",
        "flex_display",
        "kill_adb_server_on_exit",
    ):
        if isinstance(config.get(key), bool):
            normalized[key] = config[key]
    for key in ("fps", "wireless_ip"):
        if isinstance(config.get(key), str) and config[key].strip():
            normalized[key] = config[key].strip()
    return normalized


def load_config(path, logger=None):
    config_path = Path(path)
    if not config_path.exists():
        return normalize_config({})
    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            return normalize_config(json.load(config_file))
    except (OSError, json.JSONDecodeError):
        (logger or logging.getLogger(__name__)).exception("설정 파일을 읽지 못했습니다: %s", config_path.name)
        return normalize_config({})


def save_config(path, config, logger=None):
    config_path = Path(path)
    temp_path = config_path.with_suffix(f"{config_path.suffix}.tmp")
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with temp_path.open("w", encoding="utf-8", newline="\n") as config_file:
            json.dump(config, config_file, indent=2, ensure_ascii=False)
            config_file.write("\n")
            config_file.flush()
            os.fsync(config_file.fileno())
        os.replace(temp_path, config_path)
        return True
    except OSError:
        (logger or logging.getLogger(__name__)).exception("설정 파일을 저장하지 못했습니다: %s", config_path.name)
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            (logger or logging.getLogger(__name__)).exception("임시 설정 파일을 정리하지 못했습니다.")
        return False


def _first_existing(base_path, candidates):
    for candidate in candidates:
        path = base_path.joinpath(*candidate)
        if path.is_file():
            return str(path)
    return ""


def resolve_binary_paths(base_path):
    base = Path(base_path)
    adb_path = _first_existing(
        base,
        (
            ("bin", "scrcpy", "adb.exe"),
            ("bin", "adb", "adb.exe"),
            ("bin", "adb.exe"),
            ("adb.exe",),
        ),
    )
    scrcpy_path = _first_existing(
        base,
        (("bin", "scrcpy", "scrcpy.exe"), ("bin", "scrcpy.exe"), ("scrcpy.exe",)),
    )
    missing = []
    if not adb_path:
        missing.append("ADB")
    if not scrcpy_path:
        missing.append("scrcpy")
    return BinaryPaths(adb_path, scrcpy_path, tuple(missing))


def parse_wm_size(output):
    matches = re.findall(r"(?:Physical|Override) size:\s*(\d+)x(\d+)", output, re.IGNORECASE)
    if not matches:
        matches = re.findall(r"(\d+)x(\d+)", output)
    if not matches:
        return None
    width, height = matches[-1]
    return int(width), int(height)


def orient_resolution(width, height, orientation):
    short_side, long_side = sorted((int(width), int(height)))
    if orientation == "portrait":
        return short_side, long_side
    if orientation == "landscape":
        return long_side, short_side
    raise ValueError(f"지원하지 않는 화면 방향입니다: {orientation}")


def build_scrcpy_args(executable, serial, profile, options):
    validate_resolution(options.resolution, profile.orientation)
    args = [
        executable,
        "-s",
        serial,
        "--keep-active",
        "--stay-awake",
        f"--window-title={profile.display_name}",
    ]
    if options.mode == VIRTUAL_DISPLAY_MODE:
        args.extend(
            [
                f"--new-display={options.resolution}/{profile.dpi}",
                "--no-vd-system-decorations",
            ]
        )
        if options.flex_display:
            args.append("--flex-display")
    elif options.mode == MIRROR_MODE:
        width, height = (int(value) for value in options.resolution.lower().split("x", 1))
        args.append(f"--max-size={max(width, height)}")
    else:
        raise ValueError(f"지원하지 않는 실행 모드입니다: {options.mode}")

    args.append(f"--start-app=+{profile.package}")

    if options.turn_screen_off:
        args.append("--turn-screen-off")
    if options.borderless:
        args.extend(["--window-borderless", "--fullscreen"])
    if options.fps and "제한 없음" not in options.fps:
        if not options.fps.isdigit() or int(options.fps) <= 0:
            raise ValueError("FPS는 양수여야 합니다.")
        args.append(f"--max-fps={options.fps}")
    return args


def parse_scrcpy_version(output):
    match = re.search(r"^scrcpy\s+([0-9]+(?:\.[0-9]+)*)\b", output, re.MULTILINE)
    return match.group(1) if match else None


def get_scrcpy_version(executable, runner=None):
    command_runner = runner or CommandRunner()
    result = command_runner.run([executable, "--version"], timeout=5)
    if result.returncode != 0 or result.timed_out:
        return None
    return parse_scrcpy_version(f"{result.stdout}\n{result.stderr}")


def _adb_server_is_reachable(host="127.0.0.1", port=5037, timeout=0.2):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _parse_adb_server_executable(output):
    match = re.search(r'^executable_absolute_path:\s*"?(.+?)"?\s*$', output, re.MULTILINE)
    if not match:
        return ""
    return match.group(1).replace("\\\\", "\\")


def _same_windows_path(left, right):
    return os.path.normcase(os.path.normpath(os.path.abspath(left))) == os.path.normcase(
        os.path.normpath(os.path.abspath(right))
    )


class AdbServerManager:
    def __init__(self, adb_path, runner=None, server_probe=None, sleep=None, logger=None):
        self.adb_path = str(adb_path)
        self.runner = runner or CommandRunner(logger=logger)
        self.server_probe = server_probe or _adb_server_is_reachable
        self.sleep = sleep or time.sleep
        self.logger = logger or logging.getLogger(__name__)
        self.server_was_running = bool(self.server_probe())
        self.started_by_launcher = False
        self._ownership_checked = self.server_was_running
        self.logger.info("ADB server 시작 전 상태: %s", "실행 중" if self.server_was_running else "없음")

    def run(self, args, timeout=5):
        if not self._ownership_checked and self.server_probe():
            self.server_was_running = True
            self._ownership_checked = True
            self.logger.info("첫 ADB 명령 전에 시작된 공유 ADB server를 보존합니다.")
        result = self.runner.run(args, timeout=timeout)
        if not self._ownership_checked and result.returncode >= 0:
            status = self.runner.run([self.adb_path, "server-status"], timeout=5)
            server_path = _parse_adb_server_executable(status.stdout)
            self.started_by_launcher = bool(
                status.returncode == 0
                and server_path
                and _same_windows_path(server_path, self.adb_path)
            )
            self._ownership_checked = True
            if self.started_by_launcher:
                self.logger.info("런처가 시작한 bundled ADB server를 확인했습니다.")
            else:
                self.logger.info("ADB server 소유권을 획득하지 않았습니다.")
        return result

    def shutdown(self, force_preexisting=False, retries=10, retry_delay=0.1):
        should_stop = self.started_by_launcher or (force_preexisting and self.server_was_running)
        if not should_stop:
            self.logger.info("기존 공유 ADB server를 보존했습니다.")
            return False

        result = self.runner.run([self.adb_path, "kill-server"], timeout=5)
        if result.returncode != 0 or result.timed_out:
            self.logger.error("ADB server 종료 명령이 실패했습니다: %s", result.stderr.strip())
            return False
        for _ in range(retries):
            if not self.server_probe():
                self.logger.info("ADB server 종료를 확인했습니다.")
                return True
            self.sleep(retry_delay)
        self.logger.error("ADB server가 종료 뒤에도 포트 5037에서 응답합니다.")
        return False


class AdbService:
    def __init__(self, adb_path, runner=None, sleep=None, logger=None):
        self.adb_path = adb_path
        self.runner = runner or CommandRunner(logger=logger)
        self.sleep = sleep or time.sleep
        self.logger = logger or logging.getLogger(__name__)

    def list_devices(self):
        result = self.runner.run([self.adb_path, "devices", "-l"], timeout=5)
        return parse_adb_devices(result.stdout)

    def connect_wireless(self, endpoint, retries=3, retry_delay=0.5, cancel_event=None):
        for attempt in range(retries):
            if _cancel_requested(cancel_event):
                return False
            self.runner.run([self.adb_path, "connect", endpoint], timeout=10)
            if _cancel_requested(cancel_event):
                return False
            devices = self.list_devices()
            if any(device.serial == endpoint and device.state == "device" for device in devices):
                return True
            if attempt + 1 < retries:
                self.sleep(retry_delay)
        return False

    def is_package_installed(self, serial, package):
        result = self.runner.run(
            [self.adb_path, "-s", serial, "shell", "pm", "list", "packages", package],
            timeout=10,
        )
        return result.returncode == 0 and package in parse_package_list(result.stdout)

    def get_device_resolution(self, serial):
        result = self.runner.run(
            [self.adb_path, "-s", serial, "shell", "wm", "size"],
            timeout=10,
        )
        if result.returncode != 0:
            return None
        return parse_wm_size(result.stdout)

    def find_wifi_ip(self, serial, cancel_event=None):
        if _cancel_requested(cancel_event):
            return None, []
        route = self.runner.run(
            [self.adb_path, "-s", serial, "shell", "ip", "route"],
            timeout=10,
        )
        if _cancel_requested(cancel_event):
            return None, []
        addresses = self.runner.run(
            [self.adb_path, "-s", serial, "shell", "ip", "-4", "addr", "show"],
            timeout=10,
        )
        selected, candidates = select_wifi_ip(route.stdout, addresses.stdout, "")
        if not selected and not _cancel_requested(cancel_event):
            wifi = self.runner.run(
                [self.adb_path, "-s", serial, "shell", "dumpsys", "wifi"],
                timeout=20,
            )
            selected, candidates = select_wifi_ip(route.stdout, addresses.stdout, wifi.stdout)
        self.logger.info("Wi-Fi IP 후보: %s", ", ".join(candidates) if candidates else "없음")
        return selected, candidates

    def enable_tcpip(self, serial, cancel_event=None):
        if _cancel_requested(cancel_event):
            return False
        tcpip = self.runner.run(
            [self.adb_path, "-s", serial, "tcpip", "5555"],
            timeout=10,
        )
        if tcpip.returncode != 0 or tcpip.timed_out:
            return False
        if _cancel_requested(cancel_event):
            return False
        waited = self.runner.run(
            [self.adb_path, "-s", serial, "wait-for-device"],
            timeout=15,
        )
        return waited.returncode == 0 and not waited.timed_out

    def disconnect_wireless(self, endpoint, cancel_event=None):
        if _cancel_requested(cancel_event):
            return False
        self.runner.run(
            [self.adb_path, "-s", endpoint, "usb"],
            timeout=10,
        )
        if _cancel_requested(cancel_event):
            return False
        self.runner.run(
            [self.adb_path, "disconnect", endpoint],
            timeout=10,
        )
        if _cancel_requested(cancel_event):
            return False
        devices = self.list_devices()
        return not any(device.serial == endpoint and device.state == "device" for device in devices)

class ScrcpySession:
    def __init__(self, process, logger=None):
        self.process = process
        self.logger = logger or logging.getLogger(__name__)
        self._output_lock = threading.Lock()
        self._output_lines = []
        self._drain_thread = None
        if process.stdout is not None:
            self._drain_thread = threading.Thread(target=self._drain_output, daemon=True)
            self._drain_thread.start()

    def _drain_output(self):
        try:
            for line in iter(self.process.stdout.readline, ""):
                clean_line = line.rstrip()
                if clean_line:
                    self.logger.info("scrcpy: %s", clean_line)
                    with self._output_lock:
                        self._output_lines.append(clean_line)
                if not line and self.process.poll() is not None:
                    break
        except (OSError, ValueError):
            if self.process.poll() is None:
                self.logger.exception("scrcpy 로그를 읽지 못했습니다.")
            else:
                self.logger.info("종료된 scrcpy 출력 pipe 읽기를 마쳤습니다.")
    def wait_for_early_exit(self, timeout=1.5):
        try:
            exit_code = self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            return None
        if self._drain_thread:
            self._drain_thread.join(0.5)
        return exit_code

    def recent_output(self, limit=20):
        with self._output_lock:
            return "\n".join(self._output_lines[-limit:])

    def terminate(self, timeout=3):
        try:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=timeout)
        finally:
            self.close_pipes()

    def close_pipes(self, join_timeout=1):
        stdout = self.process.stdout
        if stdout is not None and not getattr(stdout, "closed", False):
            try:
                stdout.close()
            except OSError:
                self.logger.exception("scrcpy 출력 pipe를 닫지 못했습니다.")
        if self._drain_thread and self._drain_thread is not threading.current_thread():
            self._drain_thread.join(join_timeout)
            if self._drain_thread.is_alive():
                self.logger.warning("scrcpy 로그 worker가 종료되지 않았습니다.")

    def wait(self):
        try:
            return self.process.wait()
        finally:
            self.close_pipes()


class ScrcpyService:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def start(self, args):
        startupinfo = None
        if os.name == "nt" and hasattr(subprocess, "STARTUPINFO"):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            startupinfo=startupinfo,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return ScrcpySession(process, logger=self.logger)
