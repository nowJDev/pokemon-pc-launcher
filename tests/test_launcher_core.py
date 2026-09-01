# ADB와 scrcpy의 장치 독립 핵심 동작을 검증한다.

import io
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest import mock

try:
    import launcher_core
except ImportError:
    launcher_core = None

try:
    import game_profiles
except ImportError:
    game_profiles = None


CORE_UNAVAILABLE = launcher_core is None or game_profiles is None
EXTENDED_CORE_NAMES = {
    "BinaryPaths",
    "ScrcpyService",
    "ScrcpySession",
    "load_config",
    "save_config",
    "resolve_binary_paths",
    "parse_wm_size",
    "orient_resolution",
}
EXTENDED_CORE_AVAILABLE = not CORE_UNAVAILABLE and all(
    hasattr(launcher_core, name) for name in EXTENDED_CORE_NAMES
)
ADB_MANAGER_AVAILABLE = not CORE_UNAVAILABLE and hasattr(launcher_core, "AdbServerManager")
RUNTIME_CORE_NAMES = {
    "WorkerRegistry",
    "device_state_error",
    "normalize_wireless_endpoint",
}
RUNTIME_CORE_AVAILABLE = not CORE_UNAVAILABLE and all(
    hasattr(launcher_core, name) for name in RUNTIME_CORE_NAMES
)


class LauncherCoreAvailabilityTests(unittest.TestCase):
    def test_launcher_core_module_exists(self):
        self.assertIsNotNone(launcher_core)

    @unittest.skipIf(CORE_UNAVAILABLE, "핵심 모듈이 아직 없다.")
    def test_extended_core_contract_exists(self):
        missing = sorted(name for name in EXTENDED_CORE_NAMES if not hasattr(launcher_core, name))

        self.assertEqual(missing, [])

    @unittest.skipIf(CORE_UNAVAILABLE, "핵심 모듈이 아직 없다.")
    def test_adb_server_manager_contract_exists(self):
        self.assertTrue(hasattr(launcher_core, "AdbServerManager"))

    @unittest.skipIf(CORE_UNAVAILABLE, "핵심 모듈이 아직 없다.")
    def test_runtime_cleanup_contract_exists(self):
        missing = sorted(name for name in RUNTIME_CORE_NAMES if not hasattr(launcher_core, name))

        self.assertEqual(missing, [])

    @unittest.skipIf(CORE_UNAVAILABLE, "핵심 모듈이 아직 없다.")
    def test_removed_android_control_contracts_do_not_return(self):
        removed = {
            "VirtualDisplayError",
            "choose_new_display_id",
            "parse_dumpsys_launch_activity",
            "parse_resolve_activity",
            "parse_scrcpy_display_id",
            "parse_virtual_display_ids",
        }

        self.assertEqual(sorted(name for name in removed if hasattr(launcher_core, name)), [])


@unittest.skipIf(CORE_UNAVAILABLE, "핵심 모듈이 아직 없다.")
class AdbParserTests(unittest.TestCase):
    def test_parse_adb_devices_preserves_device_states(self):
        output = """List of devices attached
USB123 device product:demo model:Phone transport_id:1
USB456 unauthorized usb:2-1
192.168.0.8:5555 offline

"""

        devices = launcher_core.parse_adb_devices(output)

        self.assertEqual(
            [(device.serial, device.state) for device in devices],
            [
                ("USB123", "device"),
                ("USB456", "unauthorized"),
                ("192.168.0.8:5555", "offline"),
            ],
        )

    def test_parse_adb_devices_ignores_daemon_messages(self):
        output = """* daemon not running; starting now at tcp:5037
* daemon started successfully
List of devices attached
USB123 device
"""

        devices = launcher_core.parse_adb_devices(output)

        self.assertEqual([(device.serial, device.state) for device in devices], [("USB123", "device")])

    def test_package_list_requires_exact_package(self):
        output = "package:jp.pokemon.pokemonchampions.beta\npackage:jp.pokemon.pokemonchampions\n"

        packages = launcher_core.parse_package_list(output)

        self.assertIn("jp.pokemon.pokemonchampions", packages)
        self.assertNotIn("jp.pokemon.pokemonchampion", packages)

@unittest.skipIf(CORE_UNAVAILABLE, "핵심 모듈이 아직 없다.")
class IpDetectionTests(unittest.TestCase):
    def test_rfc1918_filter_rejects_non_private_172_and_special_addresses(self):
        accepted = ["10.0.0.1", "172.16.0.1", "172.31.255.254", "192.168.50.2"]
        rejected = [
            "172.15.0.1",
            "172.32.0.1",
            "127.0.0.1",
            "169.254.1.2",
            "224.0.0.1",
            "not-an-ip",
        ]

        for address in accepted:
            with self.subTest(address=address):
                self.assertTrue(launcher_core.is_wifi_candidate_ip(address))
        for address in rejected:
            with self.subTest(address=address):
                self.assertFalse(launcher_core.is_wifi_candidate_ip(address))

    def test_ip_selection_prefers_wlan_interface(self):
        route_output = """default via 10.0.0.1 dev rmnet_data0 src 10.0.0.20
192.168.0.0/24 dev wlan0 proto kernel scope link src 192.168.0.44
"""
        addr_output = """2: rmnet_data0: <UP>
    inet 10.0.0.20/24 scope global rmnet_data0
3: wlan0: <UP>
    inet 192.168.0.44/24 scope global wlan0
"""

        selected, candidates = launcher_core.select_wifi_ip(
            route_output,
            addr_output,
            "",
        )

        self.assertEqual(selected, "192.168.0.44")
        self.assertIn("10.0.0.20", candidates)

    def test_ip_selection_uses_wifi_dump_as_last_fallback(self):
        selected, candidates = launcher_core.select_wifi_ip(
            "",
            "",
            "mIpAddress=192.168.20.15 gateway=192.168.20.1",
        )

        self.assertEqual(selected, "192.168.20.15")
        self.assertEqual(candidates[0], "192.168.20.15")


@unittest.skipIf(CORE_UNAVAILABLE, "핵심 모듈이 아직 없다.")
class ResolutionAndConfigTests(unittest.TestCase):
    def test_resolution_validation_enforces_realistic_bounds(self):
        self.assertIsNone(launcher_core.validate_resolution("720x1280", "portrait"))

        with self.assertRaisesRegex(ValueError, "320"):
            launcher_core.validate_resolution("319x1280", "portrait")
        with self.assertRaisesRegex(ValueError, "7680"):
            launcher_core.validate_resolution("7681x4320", "landscape")
        with self.assertRaises(ValueError):
            launcher_core.validate_resolution("wide", "landscape")

    def test_resolution_orientation_mismatch_returns_warning(self):
        warning = launcher_core.validate_resolution("1920x1080", "portrait")

        self.assertIn("세로형", warning)

    def test_legacy_config_migrates_to_champions(self):
        loaded = launcher_core.normalize_config(
            {
                "wireless_ip": "192.168.0.22",
                "resolution": "1920x1080",
                "custom_resolution_enabled": True,
                "custom_width": "1600",
                "custom_height": "900",
                "fps": "60",
                "borderless": True,
                "turn_screen_off": True,
            }
        )

        self.assertEqual(loaded["last_game"], "pokemon_champions")
        self.assertEqual(loaded["game_resolutions"]["pokemon_champions"], "1920x1080")
        self.assertEqual(
            loaded["custom_resolutions"]["pokemon_champions"],
            {"width": "1600", "height": "900"},
        )
        self.assertTrue(loaded["custom_resolution_enabled"]["pokemon_champions"])
        self.assertEqual(loaded["launch_mode"], "virtual_display")
        self.assertEqual(loaded["fps"], "60")

    def test_new_config_fills_missing_profile_defaults(self):
        loaded = launcher_core.normalize_config(
            {
                "last_game": "pokemon_tcgpocket",
                "game_resolutions": {"pokemon_tcgpocket": "1080x1920"},
            }
        )

        self.assertEqual(loaded["last_game"], "pokemon_tcgpocket")
        self.assertEqual(loaded["game_resolutions"]["pokemon_tcgpocket"], "1080x1920")
        self.assertEqual(loaded["game_resolutions"]["pokemon_champions"], "1280x720")
        self.assertEqual(loaded["wireless_ip"], "192.168.0.16")
        self.assertIn("kill_adb_server_on_exit", loaded)
        self.assertFalse(loaded.get("kill_adb_server_on_exit"))
        self.assertFalse(loaded["flex_display"])

    def test_v01_config_accepts_new_flex_display_option(self):
        loaded = launcher_core.normalize_config({"flex_display": True})

        self.assertTrue(loaded["flex_display"])


@unittest.skipIf(CORE_UNAVAILABLE, "핵심 모듈이 아직 없다.")
class ScrcpyArgumentTests(unittest.TestCase):
    def test_champions_virtual_display_uses_native_app_launch(self):
        profile = game_profiles.load_game_profiles()["pokemon_champions"]
        options = launcher_core.ScrcpyOptions(
            mode="virtual_display",
            resolution="1920x1080",
            fps="60",
            borderless=True,
            turn_screen_off=True,
        )

        args = launcher_core.build_scrcpy_args(
            "scrcpy.exe",
            "USB123",
            profile,
            options,
        )

        self.assertEqual(args[:3], ["scrcpy.exe", "-s", "USB123"])
        self.assertIn("--new-display=1920x1080/320", args)
        self.assertIn("--no-vd-system-decorations", args)
        self.assertIn("--start-app=+jp.pokemon.pokemonchampions", args)
        self.assertIn("--keep-active", args)
        self.assertIn("--stay-awake", args)
        self.assertIn("--turn-screen-off", args)
        self.assertIn("--window-borderless", args)
        self.assertIn("--fullscreen", args)
        self.assertIn("--max-fps=60", args)
        self.assertIn("--window-title=Pokémon Champions", args)

    def test_pocket_virtual_display_uses_profile_dpi_and_flex(self):
        profile = game_profiles.load_game_profiles()["pokemon_tcgpocket"]
        options = launcher_core.ScrcpyOptions(
            mode="virtual_display",
            resolution="1080x1920",
            flex_display=True,
        )

        args = launcher_core.build_scrcpy_args("scrcpy.exe", "USB456", profile, options)

        self.assertIn("--new-display=1080x1920/320", args)
        self.assertIn("--start-app=+jp.pokemon.pokemontcgp", args)
        self.assertIn("--flex-display", args)

    def test_champions_mirror_uses_native_app_launch_and_max_size(self):
        profile = game_profiles.load_game_profiles()["pokemon_champions"]
        options = launcher_core.ScrcpyOptions(
            mode="mirror",
            resolution="1920x1080",
            fps="제한 없음 (기본값)",
            borderless=False,
            turn_screen_off=False,
            flex_display=True,
        )

        args = launcher_core.build_scrcpy_args(
            "scrcpy.exe",
            "USB123",
            profile,
            options,
        )

        self.assertFalse(any(arg.startswith("--new-display") for arg in args))
        self.assertNotIn("--no-vd-system-decorations", args)
        self.assertFalse(any(arg.startswith("--max-fps") for arg in args))
        self.assertIn("--max-size=1920", args)
        self.assertIn("--start-app=+jp.pokemon.pokemonchampions", args)
        self.assertNotIn("--flex-display", args)

    def test_pocket_mirror_uses_native_app_launch(self):
        profile = game_profiles.load_game_profiles()["pokemon_tcgpocket"]
        options = launcher_core.ScrcpyOptions(mode="mirror", resolution="720x1280")

        args = launcher_core.build_scrcpy_args("scrcpy.exe", "192.168.0.8:5555", profile, options)

        self.assertIn("--max-size=1280", args)
        self.assertIn("--start-app=+jp.pokemon.pokemontcgp", args)


@unittest.skipIf(CORE_UNAVAILABLE, "핵심 모듈이 아직 없다.")
class CommandAndAdbServiceTests(unittest.TestCase):
    def test_run_command_reports_timeout_separately(self):
        with mock.patch(
            "launcher_core.subprocess.run",
            side_effect=subprocess.TimeoutExpired(["adb"], 9),
        ):
            result = launcher_core.run_command(["adb"], timeout=9)

        self.assertTrue(result.timed_out)
        self.assertEqual(result.returncode, -1)
        self.assertIn("9", result.stderr)

    def test_wireless_connect_requires_device_state_after_connect(self):
        runner = mock.Mock()
        runner.run.side_effect = [
            launcher_core.CommandResult("connected to 192.168.0.8:5555", "", 0),
            launcher_core.CommandResult(
                "List of devices attached\n192.168.0.8:5555 offline\n",
                "",
                0,
            ),
            launcher_core.CommandResult("already connected", "", 0),
            launcher_core.CommandResult(
                "List of devices attached\n192.168.0.8:5555 device\n",
                "",
                0,
            ),
        ]
        service = launcher_core.AdbService("adb.exe", runner=runner, sleep=lambda _: None)

        connected = service.connect_wireless("192.168.0.8:5555", retries=2)

        self.assertTrue(connected)
        self.assertEqual(runner.run.call_count, 4)

    def test_wireless_connect_never_trusts_connect_output_alone(self):
        runner = mock.Mock()
        runner.run.side_effect = [
            launcher_core.CommandResult("connected to 192.168.0.8:5555", "", 0),
            launcher_core.CommandResult(
                "List of devices attached\n192.168.0.8:5555 unauthorized\n",
                "",
                0,
            ),
        ]
        service = launcher_core.AdbService("adb.exe", runner=runner, sleep=lambda _: None)

        connected = service.connect_wireless("192.168.0.8:5555", retries=1)

        self.assertFalse(connected)

@unittest.skipUnless(EXTENDED_CORE_AVAILABLE, "확장 core 계약이 아직 없다.")
class ConfigAndBinaryTests(unittest.TestCase):
    def test_config_round_trip_is_normalized(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            config = launcher_core.normalize_config(
                {
                    "last_game": "pokemon_tcgpocket",
                    "launch_mode": "mirror",
                    "game_resolutions": {"pokemon_tcgpocket": "1080x1920"},
                }
            )

            launcher_core.save_config(path, config)
            loaded = launcher_core.load_config(path)

        self.assertEqual(loaded["last_game"], "pokemon_tcgpocket")
        self.assertEqual(loaded["launch_mode"], "mirror")
        self.assertEqual(loaded["game_resolutions"]["pokemon_tcgpocket"], "1080x1920")

    def test_corrupt_config_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text("{broken", encoding="utf-8")

            loaded = launcher_core.load_config(path)

        self.assertEqual(loaded["last_game"], "pokemon_champions")
        self.assertEqual(loaded["launch_mode"], "virtual_display")

    def test_save_config_writes_valid_utf8_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"

            launcher_core.save_config(path, {"name": "포켓몬"})
            raw = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(raw["name"], "포켓몬")

    def test_binary_paths_use_bundled_layout_and_report_missing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / "bin" / "scrcpy").mkdir(parents=True)
            (base / "bin" / "scrcpy" / "adb.exe").write_bytes(b"adb")
            (base / "bin" / "scrcpy" / "scrcpy.exe").write_bytes(b"scrcpy")

            paths = launcher_core.resolve_binary_paths(base)
            missing = launcher_core.resolve_binary_paths(base / "empty")

        self.assertTrue(paths.adb_path.endswith("bin\\scrcpy\\adb.exe") or paths.adb_path.endswith("bin/scrcpy/adb.exe"))
        self.assertTrue(paths.scrcpy_path.endswith("bin\\scrcpy\\scrcpy.exe") or paths.scrcpy_path.endswith("bin/scrcpy/scrcpy.exe"))
        self.assertEqual(paths.missing, ())
        self.assertEqual(set(missing.missing), {"ADB", "scrcpy"})


@unittest.skipUnless(EXTENDED_CORE_AVAILABLE, "확장 core 계약이 아직 없다.")
class ExtendedAdbServiceTests(unittest.TestCase):
    def test_wm_size_prefers_override_and_orients_for_profile(self):
        parsed = launcher_core.parse_wm_size(
            "Physical size: 1080x2316\nOverride size: 900x1600\n"
        )

        self.assertEqual(parsed, (900, 1600))
        self.assertEqual(launcher_core.orient_resolution(*parsed, "landscape"), (1600, 900))
        self.assertEqual(launcher_core.orient_resolution(*parsed, "portrait"), (900, 1600))

    def test_package_installation_uses_exact_package_output(self):
        runner = mock.Mock()
        runner.run.return_value = launcher_core.CommandResult(
            "package:jp.pokemon.pokemontcgp\n",
            "",
            0,
        )
        service = launcher_core.AdbService("adb.exe", runner=runner)

        installed = service.is_package_installed("USB123", "jp.pokemon.pokemontcgp")

        self.assertTrue(installed)
        self.assertIn("pm", runner.run.call_args.args[0])

    def test_device_resolution_uses_wm_size(self):
        runner = mock.Mock()
        runner.run.return_value = launcher_core.CommandResult("Physical size: 1080x2316", "", 0)
        service = launcher_core.AdbService("adb.exe", runner=runner)

        self.assertEqual(service.get_device_resolution("USB123"), (1080, 2316))

    def test_find_wifi_ip_collects_route_and_interface_candidates(self):
        runner = mock.Mock()
        runner.run.side_effect = [
            launcher_core.CommandResult(
                "default via 10.0.0.1 dev rmnet_data0 src 10.0.0.20",
                "",
                0,
            ),
            launcher_core.CommandResult(
                "3: wlan0: <UP>\n    inet 192.168.0.44/24 scope global wlan0",
                "",
                0,
            ),
        ]
        service = launcher_core.AdbService("adb.exe", runner=runner)

        selected, candidates = service.find_wifi_ip("USB123")

        self.assertEqual(selected, "192.168.0.44")
        self.assertIn("10.0.0.20", candidates)

    def test_tcpip_mode_requires_successful_restart_and_wait(self):
        runner = mock.Mock()
        runner.run.side_effect = [
            launcher_core.CommandResult("restarting in TCP mode port: 5555", "", 0),
            launcher_core.CommandResult("", "", 0),
        ]
        service = launcher_core.AdbService("adb.exe", runner=runner)

        self.assertTrue(service.enable_tcpip("USB123"))
        self.assertEqual(runner.run.call_args_list[1].kwargs["timeout"], 15)

    def test_disconnect_wireless_disables_tcp_mode_and_verifies_absence(self):
        runner = mock.Mock()
        runner.run.side_effect = [
            launcher_core.CommandResult("restarting in USB mode", "", 0),
            launcher_core.CommandResult("disconnected 192.168.0.8:5555", "", 0),
            launcher_core.CommandResult("List of devices attached\n", "", 0),
        ]
        service = launcher_core.AdbService("adb.exe", runner=runner)

        disconnected = service.disconnect_wireless("192.168.0.8:5555")

        self.assertTrue(disconnected)
        self.assertIn("usb", runner.run.call_args_list[0].args[0])

@unittest.skipUnless(EXTENDED_CORE_AVAILABLE, "확장 core 계약이 아직 없다.")
class ScrcpySessionTests(unittest.TestCase):
    def test_early_exit_returns_exit_code(self):
        process = mock.Mock()
        process.stdout = None
        process.wait.return_value = 1
        session = launcher_core.ScrcpySession(process)

        self.assertEqual(session.wait_for_early_exit(timeout=1), 1)
        process.wait.assert_called_once_with(timeout=1)

    def test_running_process_has_no_early_exit(self):
        process = mock.Mock()
        process.stdout = None
        process.wait.side_effect = subprocess.TimeoutExpired(["scrcpy"], 1)
        session = launcher_core.ScrcpySession(process)

        self.assertIsNone(session.wait_for_early_exit(timeout=1))

    def test_normal_exit_wait_closes_stdout_pipe(self):
        process = mock.Mock()
        process.stdout = None
        process.poll.return_value = 0
        process.wait.return_value = 0
        session = launcher_core.ScrcpySession(process)
        process.stdout = mock.Mock()
        process.stdout.closed = False

        self.assertEqual(session.wait(), 0)

        process.stdout.close.assert_called_once()

    def test_terminate_waits_then_kills_only_on_timeout(self):
        process = mock.Mock()
        process.stdout = mock.Mock()
        process.stdout.closed = False
        process.poll.return_value = None
        process.wait.side_effect = [subprocess.TimeoutExpired(["scrcpy"], 3), 0]
        session = launcher_core.ScrcpySession(
            process,
        )

        session.terminate(timeout=3)

        process.terminate.assert_called_once()
        process.kill.assert_called_once()
        process.stdout.close.assert_called_once()

    def test_scrcpy_service_uses_piped_non_console_process(self):
        process = mock.Mock()
        process.stdout = io.StringIO("")
        process.poll.return_value = 0
        with mock.patch("launcher_core.subprocess.Popen", return_value=process) as popen:
            session = launcher_core.ScrcpyService().start(["scrcpy.exe", "-s", "USB123"])

        self.assertIs(session.process, process)
        self.assertEqual(popen.call_args.kwargs["stderr"], subprocess.STDOUT)
        self.assertEqual(popen.call_args.kwargs["stdout"], subprocess.PIPE)


@unittest.skipIf(CORE_UNAVAILABLE, "핵심 모듈이 아직 없다.")
class ScrcpyVersionTests(unittest.TestCase):
    def test_version_parser_accepts_official_output(self):
        output = "scrcpy 4.1 <https://github.com/Genymobile/scrcpy>\n\nDependencies:\n"

        self.assertEqual(launcher_core.parse_scrcpy_version(output), "4.1")

    def test_version_parser_rejects_unrelated_output(self):
        self.assertIsNone(launcher_core.parse_scrcpy_version("not scrcpy"))

    def test_version_query_uses_bounded_command(self):
        runner = mock.Mock()
        runner.run.return_value = launcher_core.CommandResult("scrcpy 4.1\n", "", 0)

        version = launcher_core.get_scrcpy_version("scrcpy.exe", runner=runner)

        self.assertEqual(version, "4.1")
        runner.run.assert_called_once_with(["scrcpy.exe", "--version"], timeout=5)

    def test_version_query_returns_none_on_failure(self):
        runner = mock.Mock()
        runner.run.return_value = launcher_core.CommandResult("", "missing DLL", 1)

        self.assertIsNone(launcher_core.get_scrcpy_version("scrcpy.exe", runner=runner))


@unittest.skipUnless(ADB_MANAGER_AVAILABLE, "ADB server manager가 아직 없다.")
class AdbServerManagerTests(unittest.TestCase):
    def test_launcher_owned_bundled_server_is_stopped_automatically(self):
        runner = mock.Mock()
        runner.run.side_effect = [
            launcher_core.CommandResult("List of devices attached\n", "", 0),
            launcher_core.CommandResult(
                'executable_absolute_path: "C:\\\\app\\\\bin\\\\scrcpy\\\\adb.exe"',
                "",
                0,
            ),
            launcher_core.CommandResult("", "", 0),
        ]
        probe = mock.Mock(side_effect=[False, False, False])
        manager = launcher_core.AdbServerManager(
            r"C:\app\bin\scrcpy\adb.exe",
            runner=runner,
            server_probe=probe,
            sleep=lambda _: None,
        )

        manager.run([r"C:\app\bin\scrcpy\adb.exe", "devices"], timeout=5)
        stopped = manager.shutdown(force_preexisting=False)

        self.assertTrue(manager.started_by_launcher)
        self.assertTrue(stopped)
        self.assertIn("kill-server", runner.run.call_args_list[-1].args[0])

    def test_preexisting_server_is_preserved_by_default(self):
        runner = mock.Mock()
        runner.run.return_value = launcher_core.CommandResult("List of devices attached\n", "", 0)
        manager = launcher_core.AdbServerManager(
            r"C:\app\bin\adb\adb.exe",
            runner=runner,
            server_probe=lambda: True,
            sleep=lambda _: None,
        )

        manager.run([r"C:\app\bin\adb\adb.exe", "devices"], timeout=5)
        stopped = manager.shutdown(force_preexisting=False)

        self.assertFalse(manager.started_by_launcher)
        self.assertFalse(stopped)
        self.assertEqual(runner.run.call_count, 1)

    def test_user_can_explicitly_stop_preexisting_server(self):
        runner = mock.Mock()
        runner.run.side_effect = [
            launcher_core.CommandResult("List of devices attached\n", "", 0),
            launcher_core.CommandResult("", "", 0),
        ]
        probe = mock.Mock(side_effect=[True, False])
        manager = launcher_core.AdbServerManager(
            r"C:\app\bin\adb\adb.exe",
            runner=runner,
            server_probe=probe,
            sleep=lambda _: None,
        )

        manager.run([r"C:\app\bin\adb\adb.exe", "devices"], timeout=5)
        stopped = manager.shutdown(force_preexisting=True)

        self.assertTrue(stopped)
        self.assertIn("kill-server", runner.run.call_args_list[-1].args[0])

    def test_different_server_executable_is_not_claimed(self):
        runner = mock.Mock()
        runner.run.side_effect = [
            launcher_core.CommandResult("List of devices attached\n", "", 0),
            launcher_core.CommandResult(
                'executable_absolute_path: "C:\\\\Android\\\\platform-tools\\\\adb.exe"',
                "",
                0,
            ),
        ]
        manager = launcher_core.AdbServerManager(
            r"C:\app\bin\adb\adb.exe",
            runner=runner,
            server_probe=lambda: False,
            sleep=lambda _: None,
        )

        manager.run([r"C:\app\bin\adb\adb.exe", "devices"], timeout=5)
        stopped = manager.shutdown(force_preexisting=False)

        self.assertFalse(manager.started_by_launcher)
        self.assertFalse(stopped)
        self.assertEqual(runner.run.call_count, 2)

    def test_server_started_by_another_tool_before_first_command_is_preserved(self):
        runner = mock.Mock()
        runner.run.return_value = launcher_core.CommandResult(
            "List of devices attached\n",
            "",
            0,
        )
        probe = mock.Mock(side_effect=[False, True])
        manager = launcher_core.AdbServerManager(
            r"C:\app\bin\adb\adb.exe",
            runner=runner,
            server_probe=probe,
            sleep=lambda _: None,
        )

        manager.run([r"C:\app\bin\adb\adb.exe", "devices"], timeout=5)
        stopped = manager.shutdown(force_preexisting=False)

        self.assertTrue(manager.server_was_running)
        self.assertFalse(manager.started_by_launcher)
        self.assertFalse(stopped)
        self.assertEqual(runner.run.call_count, 1)


@unittest.skipUnless(RUNTIME_CORE_AVAILABLE, "런타임 정리 계약이 아직 없다.")
class RuntimeCleanupTests(unittest.TestCase):
    def test_device_state_errors_are_explicit(self):
        self.assertIsNone(launcher_core.device_state_error("device"))
        self.assertIn("USB 디버깅 허용", launcher_core.device_state_error("unauthorized"))
        self.assertIn("offline", launcher_core.device_state_error("offline"))
        self.assertIn("정상 상태", launcher_core.device_state_error("recovery"))

    def test_wireless_endpoint_accepts_only_rfc1918_ipv4(self):
        self.assertEqual(
            launcher_core.normalize_wireless_endpoint("192.168.0.8"),
            "192.168.0.8:5555",
        )
        self.assertEqual(
            launcher_core.normalize_wireless_endpoint("10.0.0.2:5556"),
            "10.0.0.2:5556",
        )
        with self.assertRaises(ValueError):
            launcher_core.normalize_wireless_endpoint("8.8.8.8")
        with self.assertRaises(ValueError):
            launcher_core.normalize_wireless_endpoint("bad-ip")

    def test_worker_registry_joins_completed_workers(self):
        registry = launcher_core.WorkerRegistry()
        completed = threading.Event()

        registry.start("quick-worker", completed.set)
        alive = registry.join_all(timeout=1)

        self.assertTrue(completed.is_set())
        self.assertEqual(alive, [])

    def test_worker_registry_reports_workers_that_do_not_finish_in_time(self):
        registry = launcher_core.WorkerRegistry()
        release = threading.Event()
        registry.start("blocked-worker", lambda: release.wait(1))

        alive = registry.join_all(timeout=0)
        release.set()
        registry.join_all(timeout=1)

        self.assertEqual(alive, ["blocked-worker"])

    def test_wireless_retry_stops_when_shutdown_is_requested(self):
        runner = mock.Mock()
        cancelled = threading.Event()
        cancelled.set()
        service = launcher_core.AdbService("adb.exe", runner=runner, sleep=lambda _: None)

        connected = service.connect_wireless(
            "192.168.0.8:5555",
            cancel_event=cancelled,
        )

        self.assertFalse(connected)
        runner.run.assert_not_called()

if __name__ == "__main__":
    unittest.main()
