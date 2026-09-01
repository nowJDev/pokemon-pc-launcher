# 멀티게임 Pokémon PC Launcher의 Tkinter 사용자 인터페이스를 제공한다.

import ctypes
import logging
import os
from pathlib import Path
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from game_profiles import get_profile_by_display_name, load_game_profiles
from launcher_core import (
    DEFAULT_FPS,
    MIRROR_MODE,
    SUPPORTED_SCRCPY_VERSION,
    VIRTUAL_DISPLAY_MODE,
    AdbServerManager,
    AdbService,
    ScrcpyOptions,
    ScrcpyService,
    WorkerRegistry,
    build_scrcpy_args,
    device_state_error,
    get_scrcpy_version,
    load_config,
    normalize_wireless_endpoint,
    orient_resolution,
    resolve_binary_paths,
    save_config,
    validate_resolution,
)


APP_NAME = "Pokémon PC Launcher"
APP_VERSION = "0.2"
MODE_LABELS = {
    VIRTUAL_DISPLAY_MODE: "Virtual Display",
    MIRROR_MODE: "기본 화면 미러링",
}
MODE_KEYS = {label: key for key, label in MODE_LABELS.items()}
FPS_VALUES = (DEFAULT_FPS, "30", "45", "60", "90", "120", "144")


def get_application_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def configure_logger(application_dir):
    log_path = Path(application_dir) / "launcher.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(threadName)s %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8")],
        force=True,
    )
    logger = logging.getLogger(APP_NAME)
    logger.info("%s %s 시작", APP_NAME, APP_VERSION)
    return logger


def set_windows_app_id(logger):
    if os.name != "nt":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            f"nowJDev.PokemonPCLauncher.{APP_VERSION}"
        )
    except (AttributeError, OSError):
        logger.exception("Windows AppUserModelID 설정에 실패했습니다.")


class AppLauncher:
    def __init__(self, root, application_dir, logger):
        self.root = root
        self.application_dir = Path(application_dir)
        self.logger = logger
        self.config_path = self.application_dir / "config.json"
        self.icon_path = self.application_dir / "pokemon_icon.ico"
        if not self.icon_path.is_file():
            self.icon_path = self.application_dir / "bin" / "scrcpy" / "pokemon_icon.ico"
        self.profiles = load_game_profiles()
        self.config = load_config(self.config_path, logger=self.logger)
        self.current_profile_key = self.config["last_game"]
        self.binary_paths = resolve_binary_paths(self.application_dir)
        self.workers = WorkerRegistry()
        self.closing = threading.Event()
        self.session_lock = threading.Lock()
        self.scrcpy_session = None
        self.devices_by_label = {}
        self.created_wireless_endpoints = set()
        self._scrcpy_icon_handle = None

        self.adb_manager = None
        self.adb_service = None
        self.scrcpy_service = None
        if not self.binary_paths.missing:
            self.adb_manager = AdbServerManager(
                self.binary_paths.adb_path,
                logger=self.logger,
            )
            self.adb_service = AdbService(
                self.binary_paths.adb_path,
                runner=self.adb_manager,
                logger=self.logger,
            )
            self.scrcpy_service = ScrcpyService(logger=self.logger)
            os.environ["ADB"] = self.binary_paths.adb_path

        self._create_variables()
        self._build_ui()
        self._load_selected_game_settings()
        self.root.protocol("WM_DELETE_WINDOW", self.request_shutdown)

        if self.binary_paths.missing:
            missing = ", ".join(self.binary_paths.missing)
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    APP_NAME,
                    f"필수 실행 파일을 찾을 수 없습니다: {missing}\n"
                    "프로그램 폴더의 bin 디렉터리를 확인해 주세요.",
                ),
            )
            self.launch_button.configure(state="disabled")
            self._set_status(f"필수 실행 파일 없음: {missing}")
        else:
            self.root.after(100, self._check_scrcpy_version)

    def _create_variables(self):
        initial_key = self.config["last_game"]
        initial_profile = self.profiles[initial_key]
        self.game_var = tk.StringVar(value=initial_profile.display_name)
        self.device_var = tk.StringVar()
        self.install_status_var = tk.StringVar(value="설치 여부: 기기를 선택해 주세요.")
        self.wireless_ip_var = tk.StringVar(value=self.config["wireless_ip"])
        self.resolution_var = tk.StringVar()
        self.custom_enabled_var = tk.BooleanVar()
        self.custom_width_var = tk.StringVar()
        self.custom_height_var = tk.StringVar()
        self.mode_var = tk.StringVar(value=MODE_LABELS[self.config["launch_mode"]])
        self.fps_var = tk.StringVar(value=self.config["fps"])
        self.borderless_var = tk.BooleanVar(value=self.config["borderless"])
        self.turn_screen_off_var = tk.BooleanVar(value=self.config["turn_screen_off"])
        self.flex_display_var = tk.BooleanVar(value=self.config["flex_display"])
        self.kill_adb_server_var = tk.BooleanVar(
            value=self.config["kill_adb_server_on_exit"]
        )
        self.status_var = tk.StringVar(value="준비되었습니다.")

    def _build_ui(self):
        self.root.geometry("520x820")
        self.root.minsize(500, 775)
        self.root.title(f"{APP_NAME} {APP_VERSION}")
        self.root.columnconfigure(0, weight=1)

        container = ttk.Frame(self.root, padding=12)
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)

        game_frame = ttk.LabelFrame(container, text="1. 실행할 게임 선택", padding=10)
        game_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        game_frame.columnconfigure(0, weight=1)
        self.game_combo = ttk.Combobox(
            game_frame,
            state="readonly",
            textvariable=self.game_var,
            values=[profile.display_name for profile in self.profiles.values()],
        )
        self.game_combo.grid(row=0, column=0, sticky="ew")
        self.game_combo.bind("<<ComboboxSelected>>", self._on_game_changed)

        device_frame = ttk.LabelFrame(container, text="2. 연결할 기기 선택", padding=10)
        device_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        device_frame.columnconfigure(0, weight=1)
        self.device_combo = ttk.Combobox(
            device_frame,
            state="readonly",
            textvariable=self.device_var,
        )
        self.device_combo.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.device_combo.bind("<<ComboboxSelected>>", self._on_device_changed)
        ttk.Button(device_frame, text="새로고침", command=self.refresh_devices).grid(
            row=0, column=1
        )
        ttk.Label(device_frame, textvariable=self.install_status_var).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(6, 0)
        )

        wireless_frame = ttk.LabelFrame(
            container,
            text="3. 무선 연결 및 설정",
            padding=10,
        )
        wireless_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        wireless_frame.columnconfigure(1, weight=1)
        ttk.Label(wireless_frame, text="IP 주소").grid(row=0, column=0, padx=(0, 8))
        ttk.Entry(wireless_frame, textvariable=self.wireless_ip_var).grid(
            row=0, column=1, sticky="ew", padx=(0, 8)
        )
        ttk.Button(wireless_frame, text="연결", command=self.connect_wireless).grid(
            row=0, column=2, padx=(0, 4)
        )
        ttk.Button(wireless_frame, text="연결 해제", command=self.disconnect_wireless).grid(
            row=0, column=3
        )
        ttk.Button(
            wireless_frame,
            text="USB 기기를 무선 ADB로 자동 설정",
            command=self.configure_wireless_from_usb,
        ).grid(row=1, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        ttk.Label(
            wireless_frame,
            text="무선 ADB 사용 후에는 공용 Wi-Fi에서 연결을 해제하세요.",
        ).grid(row=2, column=0, columnspan=4, sticky="w", pady=(6, 0))

        display_frame = ttk.LabelFrame(
            container,
            text="4. 해상도 및 화면 설정",
            padding=10,
        )
        display_frame.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        display_frame.columnconfigure(1, weight=1)
        ttk.Label(display_frame, text="해상도").grid(row=0, column=0, sticky="w")
        self.resolution_combo = ttk.Combobox(
            display_frame,
            state="readonly",
            textvariable=self.resolution_var,
        )
        self.resolution_combo.grid(row=0, column=1, sticky="ew", padx=(8, 8))
        ttk.Button(
            display_frame,
            text="기기 원본",
            command=self.use_device_resolution,
        ).grid(row=0, column=2)

        ttk.Checkbutton(
            display_frame,
            text="사용자 지정",
            variable=self.custom_enabled_var,
            command=self._update_custom_state,
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))
        custom_frame = ttk.Frame(display_frame)
        custom_frame.grid(row=1, column=1, columnspan=2, sticky="w", padx=(8, 0), pady=(8, 0))
        self.custom_width_entry = ttk.Entry(
            custom_frame,
            width=8,
            textvariable=self.custom_width_var,
        )
        self.custom_width_entry.grid(row=0, column=0)
        ttk.Label(custom_frame, text=" x ").grid(row=0, column=1)
        self.custom_height_entry = ttk.Entry(
            custom_frame,
            width=8,
            textvariable=self.custom_height_var,
        )
        self.custom_height_entry.grid(row=0, column=2)

        ttk.Label(display_frame, text="실행 모드").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.mode_combo = ttk.Combobox(
            display_frame,
            state="readonly",
            textvariable=self.mode_var,
            values=list(MODE_KEYS),
        )
        self.mode_combo.grid(
            row=2,
            column=1,
            columnspan=2,
            sticky="ew",
            padx=(8, 0),
            pady=(8, 0),
        )
        self.mode_combo.bind("<<ComboboxSelected>>", self._update_flex_state)
        self.flex_check = ttk.Checkbutton(
            display_frame,
            text="창 크기에 자동 맞춤 (Flex Display)",
            variable=self.flex_display_var,
        )
        self.flex_check.grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))
        ttk.Label(display_frame, text="최대 전송 FPS").grid(
            row=4,
            column=0,
            sticky="w",
            pady=(8, 0),
        )
        ttk.Combobox(
            display_frame,
            state="readonly",
            textvariable=self.fps_var,
            values=FPS_VALUES,
        ).grid(row=4, column=1, columnspan=2, sticky="ew", padx=(8, 0), pady=(8, 0))
        ttk.Checkbutton(
            display_frame,
            text="Borderless Fullscreen",
            variable=self.borderless_var,
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Checkbutton(
            display_frame,
            text="스마트폰 실제 화면 끄기",
            variable=self.turn_screen_off_var,
        ).grid(row=6, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(
            display_frame,
            text="종료 시 기존 ADB 서버도 종료 (고급)",
            variable=self.kill_adb_server_var,
        ).grid(row=7, column=0, columnspan=3, sticky="w")
        self._update_flex_state()

        launch_frame = ttk.LabelFrame(container, text="5. 게임 실행", padding=10)
        launch_frame.grid(row=4, column=0, sticky="ew", pady=(0, 8))
        launch_frame.columnconfigure(0, weight=1)
        self.launch_button = ttk.Button(
            launch_frame,
            text="게임 실행",
            command=self.launch_game,
        )
        self.launch_button.grid(row=0, column=0, sticky="ew")

        ttk.Label(container, textvariable=self.status_var, wraplength=480).grid(
            row=5, column=0, sticky="ew"
        )

    def _post_ui(self, callback, allow_during_shutdown=False):
        if self.closing.is_set() and not allow_during_shutdown:
            return
        try:
            self.root.after(0, callback)
        except tk.TclError:
            self.logger.info("종료된 Tkinter 창에 대한 UI 갱신을 생략했습니다.")

    def _set_status(self, message):
        self.status_var.set(message)

    def _start_worker(self, name, target, failure_message):
        if self.closing.is_set():
            return

        def guarded_target():
            try:
                target()
            except Exception:
                self.logger.exception("%s 작업 중 예외가 발생했습니다.", name)
                self._post_ui(lambda: messagebox.showerror(APP_NAME, failure_message))

        self.workers.start(name, guarded_target)

    def _selected_profile(self):
        return get_profile_by_display_name(self.game_var.get())

    def _selected_device(self):
        return self.devices_by_label.get(self.device_var.get())

    def _store_current_game_settings(self):
        profile_key = self.current_profile_key
        if profile_key not in self.profiles:
            return
        self.config["game_resolutions"][profile_key] = self.resolution_var.get()
        self.config["custom_resolution_enabled"][profile_key] = self.custom_enabled_var.get()
        self.config["custom_resolutions"][profile_key] = {
            "width": self.custom_width_var.get(),
            "height": self.custom_height_var.get(),
        }

    def _load_selected_game_settings(self):
        profile = self._selected_profile()
        self.resolution_combo.configure(values=profile.resolutions)
        selected = self.config["game_resolutions"].get(profile.key, profile.default_resolution)
        if selected not in profile.resolutions:
            selected = profile.default_resolution
        self.resolution_var.set(selected)
        self.custom_enabled_var.set(
            self.config["custom_resolution_enabled"].get(profile.key, False)
        )
        custom = self.config["custom_resolutions"].get(profile.key, {})
        width, height = profile.default_resolution.split("x", 1)
        self.custom_width_var.set(str(custom.get("width", width)))
        self.custom_height_var.set(str(custom.get("height", height)))
        self._update_custom_state()
        self.current_profile_key = profile.key
        self.root.title(f"{APP_NAME} {APP_VERSION} - {profile.display_name}")
        self.launch_button.configure(text=f"{profile.display_name} 실행")
        self.logger.info(
            "선택 게임: %s, package=%s, orientation=%s",
            profile.display_name,
            profile.package,
            profile.orientation,
        )

    def _on_game_changed(self, _event=None):
        self._store_current_game_settings()
        profile = self._selected_profile()
        self.config["last_game"] = profile.key
        self._load_selected_game_settings()
        self._on_device_changed()

    def _update_custom_state(self):
        state = "normal" if self.custom_enabled_var.get() else "disabled"
        self.resolution_combo.configure(
            state="disabled" if self.custom_enabled_var.get() else "readonly"
        )
        self.custom_width_entry.configure(state=state)
        self.custom_height_entry.configure(state=state)

    def _update_flex_state(self, _event=None):
        mode = MODE_KEYS.get(self.mode_var.get())
        self.flex_check.configure(
            state="normal" if mode == VIRTUAL_DISPLAY_MODE else "disabled"
        )

    def _check_scrcpy_version(self):
        def work():
            version = get_scrcpy_version(self.binary_paths.scrcpy_path)
            if version == SUPPORTED_SCRCPY_VERSION:
                self.logger.info("scrcpy 버전 확인: %s", version)
            else:
                found = version or "확인할 수 없음"
                self.logger.warning(
                    "지원하지 않는 scrcpy 버전: expected=%s actual=%s",
                    SUPPORTED_SCRCPY_VERSION,
                    found,
                )
                message = (
                    f"{APP_NAME} {APP_VERSION}는 scrcpy "
                    f"{SUPPORTED_SCRCPY_VERSION}을 기준으로 개발되었습니다.\n\n"
                    f"현재 발견된 버전:\n{found}"
                )
                self._post_ui(lambda: messagebox.showwarning(APP_NAME, message))
            self._post_ui(self.refresh_devices)

        self._start_worker(
            "scrcpy-version-check",
            work,
            "scrcpy 버전을 확인하지 못했습니다.",
        )

    def refresh_devices(self):
        if not self.adb_service:
            return
        self._set_status("ADB 기기 목록을 확인하는 중입니다.")

        def work():
            devices = self.adb_service.list_devices()

            def apply():
                old_serial = None
                selected = self._selected_device()
                if selected:
                    old_serial = selected.serial
                self.devices_by_label = {
                    f"{device.serial}  [{device.state}]": device for device in devices
                }
                labels = list(self.devices_by_label)
                self.device_combo.configure(values=labels)
                matching_label = next(
                    (
                        label
                        for label, device in self.devices_by_label.items()
                        if device.serial == old_serial
                    ),
                    None,
                )
                self.device_var.set(matching_label or (labels[0] if labels else ""))
                self._set_status(
                    f"ADB 기기 {len(devices)}개를 확인했습니다."
                    if devices
                    else "연결된 ADB 기기가 없습니다."
                )
                self._on_device_changed()

            self._post_ui(apply)

        self._start_worker("device-refresh", work, "ADB 기기 목록을 읽지 못했습니다.")

    def _on_device_changed(self, _event=None):
        device = self._selected_device()
        if not device:
            self.install_status_var.set("설치 여부: 기기를 선택해 주세요.")
            return
        state_message = device_state_error(device.state)
        if state_message:
            self.install_status_var.set(state_message)
            return
        profile = self._selected_profile()
        self.install_status_var.set("설치 여부 확인 중입니다.")

        def work():
            installed = self.adb_service.is_package_installed(device.serial, profile.package)
            text = f"{profile.display_name}: {'설치됨' if installed else '설치되지 않음'}"
            self._post_ui(lambda: self.install_status_var.set(text))

        self._start_worker("package-check", work, "앱 설치 여부를 확인하지 못했습니다.")

    def connect_wireless(self):
        try:
            endpoint = normalize_wireless_endpoint(self.wireless_ip_var.get())
        except ValueError as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        self.wireless_ip_var.set(endpoint)
        self._set_status(f"{endpoint} 연결을 검증하는 중입니다.")

        def work():
            connected = self.adb_service.connect_wireless(
                endpoint,
                cancel_event=self.closing,
            )
            if not connected:
                self._post_ui(
                    lambda: messagebox.showerror(
                        APP_NAME,
                        "무선 ADB 연결 후 device 상태를 확인하지 못했습니다.",
                    )
                )
                self._post_ui(lambda: self._set_status("무선 ADB 연결에 실패했습니다."))
                return
            self.created_wireless_endpoints.add(endpoint)
            self.logger.info("무선 ADB 연결 검증 완료: %s", endpoint)
            self._post_ui(self.refresh_devices)
            self._post_ui(lambda: self._set_status(f"무선 ADB 연결 완료: {endpoint}"))

        self._start_worker("wireless-connect", work, "무선 ADB 연결 중 오류가 발생했습니다.")

    def disconnect_wireless(self):
        try:
            endpoint = normalize_wireless_endpoint(self.wireless_ip_var.get())
        except ValueError as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        self._set_status(f"{endpoint} 연결을 해제하는 중입니다.")

        def work():
            disconnected = self.adb_service.disconnect_wireless(
                endpoint,
                cancel_event=self.closing,
            )
            if disconnected:
                self.created_wireless_endpoints.discard(endpoint)
                message = f"무선 ADB 연결 해제 완료: {endpoint}"
            else:
                message = f"무선 ADB 연결 해제를 확인하지 못했습니다: {endpoint}"
            self.logger.info(message)
            self._post_ui(lambda: self._set_status(message))
            self._post_ui(self.refresh_devices)

        self._start_worker("wireless-disconnect", work, "무선 ADB 연결 해제 중 오류가 발생했습니다.")

    def configure_wireless_from_usb(self):
        device = self._selected_device()
        if not device:
            messagebox.showerror(APP_NAME, "USB 기기를 선택해 주세요.")
            return
        state_message = device_state_error(device.state)
        if state_message:
            messagebox.showerror(APP_NAME, state_message)
            return
        if device.is_wireless:
            messagebox.showerror(APP_NAME, "USB로 연결된 기기를 선택해 주세요.")
            return
        self._set_status("USB 기기를 무선 ADB로 설정하는 중입니다.")

        def work():
            if not self.adb_service.enable_tcpip(device.serial, cancel_event=self.closing):
                raise RuntimeError("ADB TCP/IP 5555 모드를 활성화하지 못했습니다.")
            address, candidates = self.adb_service.find_wifi_ip(
                device.serial,
                cancel_event=self.closing,
            )
            if not address:
                raise RuntimeError("스마트폰의 Wi-Fi IP 주소를 찾지 못했습니다.")
            endpoint = f"{address}:5555"
            if not self.adb_service.connect_wireless(
                endpoint,
                cancel_event=self.closing,
            ):
                raise RuntimeError("무선 연결 후 ADB device 상태를 확인하지 못했습니다.")
            self.created_wireless_endpoints.add(endpoint)
            self.logger.info("USB→Wi-Fi ADB 설정 완료: %s, 후보=%s", endpoint, candidates)

            def apply():
                self.wireless_ip_var.set(endpoint)
                self._set_status(f"USB→Wi-Fi ADB 설정 완료: {endpoint}")
                self.refresh_devices()

            self._post_ui(apply)

        self._start_worker(
            "wireless-auto-setup",
            work,
            "USB→Wi-Fi ADB 자동 설정에 실패했습니다. launcher.log를 확인해 주세요.",
        )

    def use_device_resolution(self):
        device = self._selected_device()
        if not device:
            messagebox.showerror(APP_NAME, "기기를 선택해 주세요.")
            return
        state_message = device_state_error(device.state)
        if state_message:
            messagebox.showerror(APP_NAME, state_message)
            return
        profile = self._selected_profile()

        def work():
            size = self.adb_service.get_device_resolution(device.serial)
            if not size:
                raise RuntimeError("기기 원본 해상도를 읽지 못했습니다.")
            width, height = orient_resolution(*size, profile.orientation)

            def apply():
                self.custom_enabled_var.set(True)
                self.custom_width_var.set(str(width))
                self.custom_height_var.set(str(height))
                self._update_custom_state()
                self._set_status(f"기기 원본 해상도 적용: {width}x{height}")

            self._post_ui(apply)

        self._start_worker("device-resolution", work, "기기 원본 해상도를 가져오지 못했습니다.")

    def _validated_launch_selection(self):
        profile = self._selected_profile()
        device = self._selected_device()
        if not device:
            raise ValueError("연결할 Android 기기를 선택해 주세요.")
        state_message = device_state_error(device.state)
        if state_message:
            raise ValueError(state_message)
        if self.custom_enabled_var.get():
            resolution = f"{self.custom_width_var.get()}x{self.custom_height_var.get()}"
        else:
            resolution = self.resolution_var.get()
        warning = validate_resolution(resolution, profile.orientation)
        if warning and not messagebox.askyesno(APP_NAME, f"{warning}\n그래도 실행할까요?"):
            return None
        mode = MODE_KEYS.get(self.mode_var.get())
        if mode is None:
            raise ValueError("실행 모드를 선택해 주세요.")
        return profile, device, resolution, mode

    def launch_game(self):
        if self.binary_paths.missing:
            messagebox.showerror(APP_NAME, "ADB와 scrcpy 실행 파일을 확인해 주세요.")
            return
        try:
            selection = self._validated_launch_selection()
        except (KeyError, ValueError) as exc:
            messagebox.showerror(APP_NAME, str(exc))
            return
        if selection is None:
            return
        profile, selected_device, resolution, mode = selection
        fps = self.fps_var.get()
        borderless = self.borderless_var.get()
        turn_screen_off = self.turn_screen_off_var.get()
        flex_display = self.flex_display_var.get()
        self.launch_button.configure(state="disabled")
        self._set_status("게임 실행 전 검증을 시작합니다.")

        def work():
            session = None
            started = False
            try:
                devices = {device.serial: device for device in self.adb_service.list_devices()}
                device = devices.get(selected_device.serial)
                if not device:
                    raise RuntimeError("선택한 기기가 더 이상 연결되어 있지 않습니다.")
                state_message = device_state_error(device.state)
                if state_message:
                    raise RuntimeError(state_message)
                if not self.adb_service.is_package_installed(device.serial, profile.package):
                    raise RuntimeError(
                        f"{profile.display_name}이 선택한 스마트폰에 설치되어 있지 않습니다."
                    )
                options = ScrcpyOptions(
                    mode=mode,
                    resolution=resolution,
                    fps=fps,
                    borderless=borderless,
                    turn_screen_off=turn_screen_off,
                    flex_display=flex_display,
                )
                args = build_scrcpy_args(
                    self.binary_paths.scrcpy_path,
                    device.serial,
                    profile,
                    options,
                )
                self.logger.info(
                    "scrcpy 시작: device=%s mode=%s resolution=%s",
                    device.serial,
                    mode,
                    resolution,
                )
                session = self.scrcpy_service.start(args)
                with self.session_lock:
                    self.scrcpy_session = session
                early_exit = session.wait_for_early_exit()
                if early_exit is not None:
                    details = session.recent_output()
                    suffix = f"\n\n{details}" if details else ""
                    raise RuntimeError(
                        f"scrcpy가 시작 직후 종료되었습니다. exit code: {early_exit}{suffix}"
                    )
                started = True
                self.logger.info("scrcpy session 시작 확인: %s", profile.display_name)
                self._post_ui(lambda: self._on_game_started(profile))
                exit_code = session.wait()
                self.logger.info("scrcpy 종료: exit_code=%s", exit_code)
                if exit_code != 0 and not self.closing.is_set():
                    details = session.recent_output()
                    suffix = f"\n\n{details}" if details else ""
                    message = f"scrcpy가 오류로 종료되었습니다. exit code: {exit_code}{suffix}"
                    self._post_ui(lambda: messagebox.showerror(APP_NAME, message))
            except Exception:
                self.logger.exception("게임 실행에 실패했습니다.")
                message = str(sys.exc_info()[1])
                self._post_ui(lambda: messagebox.showerror(APP_NAME, message))
            finally:
                if session and not started:
                    session.terminate()
                    self.logger.info("실패한 scrcpy process 정리 완료")
                with self.session_lock:
                    if self.scrcpy_session is session:
                        self.scrcpy_session = None
                if started:
                    self._post_ui(self.request_shutdown)
                else:
                    self._post_ui(self._restore_after_launch_failure)

        self.workers.start("game-launch", work)

    def _on_game_started(self, profile):
        self._set_status(f"{profile.display_name} 실행 중입니다.")
        self._apply_scrcpy_window_icon(profile.display_name)
        self.root.withdraw()

    def _restore_after_launch_failure(self):
        self.launch_button.configure(state="normal")
        self._set_status("게임 실행에 실패했습니다. launcher.log를 확인해 주세요.")

    def _apply_scrcpy_window_icon(self, window_title, retries=10):
        if os.name != "nt" or not self.icon_path.is_file() or self.closing.is_set():
            return
        user32 = ctypes.windll.user32
        window = user32.FindWindowW(None, window_title)
        if not window:
            if retries > 0:
                self.root.after(
                    250,
                    lambda: self._apply_scrcpy_window_icon(window_title, retries - 1),
                )
            return
        image_icon = 1
        load_from_file = 0x0010
        icon = user32.LoadImageW(None, str(self.icon_path), image_icon, 0, 0, load_from_file)
        if icon:
            user32.SendMessageW(window, 0x0080, 0, icon)
            user32.SendMessageW(window, 0x0080, 1, icon)
            self._scrcpy_icon_handle = icon
            self.logger.info("scrcpy window icon 적용 완료")

    def _collect_config(self):
        self._store_current_game_settings()
        profile = self._selected_profile()
        self.config.update(
            {
                "last_game": profile.key,
                "launch_mode": MODE_KEYS.get(self.mode_var.get(), VIRTUAL_DISPLAY_MODE),
                "fps": self.fps_var.get(),
                "borderless": self.borderless_var.get(),
                "turn_screen_off": self.turn_screen_off_var.get(),
                "flex_display": self.flex_display_var.get(),
                "kill_adb_server_on_exit": self.kill_adb_server_var.get(),
                "wireless_ip": self.wireless_ip_var.get(),
            }
        )
        return self.config

    def request_shutdown(self):
        if self.closing.is_set():
            return
        self.closing.set()
        self.logger.info("정상 종료 sequence 시작")
        config = self._collect_config()
        force_adb_shutdown = self.kill_adb_server_var.get()
        try:
            self.root.withdraw()
        except tk.TclError:
            self.logger.info("이미 닫힌 Tkinter 창을 숨길 수 없습니다.")
        self.workers.start(
            "shutdown-cleanup",
            self._cleanup,
            config,
            force_adb_shutdown,
        )

    def _cleanup(self, config, force_adb_shutdown):
        try:
            self._cleanup_steps(config, force_adb_shutdown)
        except Exception:
            self.logger.exception("정상 종료 sequence 중 예외가 발생했습니다.")
        finally:
            self.logger.info("child process 종료 및 정상 종료 sequence 완료")
            for handler in logging.getLogger().handlers:
                try:
                    handler.flush()
                except (OSError, ValueError):
                    self.logger.exception("로그 handler flush에 실패했습니다.")
            self._post_ui(self._finalize_shutdown, allow_during_shutdown=True)

    def _cleanup_steps(self, config, force_adb_shutdown):
        with self.session_lock:
            session = self.scrcpy_session
        if session:
            try:
                session.terminate(timeout=3)
                self.logger.info("scrcpy process 및 pipe 종료 완료")
            except Exception:
                self.logger.exception("scrcpy process 종료 중 오류가 발생했습니다.")
        else:
            self.logger.info("종료할 scrcpy process가 없습니다.")

        alive_workers = self.workers.join_all(timeout=22)
        if alive_workers:
            self.logger.warning("종료되지 않은 worker thread: %s", ", ".join(alive_workers))
        else:
            self.logger.info("launcher worker thread 종료 완료")

        for endpoint in sorted(self.created_wireless_endpoints):
            try:
                disconnected = self.adb_service.disconnect_wireless(endpoint)
                self.logger.info("종료 시 ADB disconnect %s: %s", endpoint, disconnected)
            except Exception:
                self.logger.exception("종료 시 ADB connection 해제 실패: %s", endpoint)

        saved = save_config(self.config_path, config, logger=self.logger)
        self.logger.info("config 저장 결과: %s", saved)

        if self.adb_manager:
            try:
                stopped = self.adb_manager.shutdown(force_preexisting=force_adb_shutdown)
                self.logger.info("ADB server 종료 결과: %s", stopped)
            except Exception:
                self.logger.exception("ADB server 종료 중 오류가 발생했습니다.")

    def _finalize_shutdown(self):
        try:
            self.root.destroy()
        finally:
            logging.shutdown()


def main():
    application_dir = get_application_dir()
    logger = configure_logger(application_dir)
    set_windows_app_id(logger)
    root = tk.Tk()
    icon_path = application_dir / "pokemon_icon.ico"
    if not icon_path.is_file():
        icon_path = application_dir / "bin" / "scrcpy" / "pokemon_icon.ico"
    if icon_path.is_file():
        try:
            root.iconbitmap(str(icon_path))
        except tk.TclError:
            logger.exception("런처 window icon을 적용하지 못했습니다.")
    AppLauncher(root, application_dir, logger)
    root.mainloop()
    logger.info("Tkinter mainloop 종료")


if __name__ == "__main__":
    main()
