# GUI 진입점의 버전과 금지된 하드코딩 제거를 검증한다.

from pathlib import Path
import unittest

import pokemon_launcher


class LauncherGuiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path(pokemon_launcher.__file__).read_text(encoding="utf-8")

    def test_app_identity_uses_stabilization_version(self):
        self.assertTrue(hasattr(pokemon_launcher, "APP_NAME"))
        self.assertTrue(hasattr(pokemon_launcher, "APP_VERSION"))
        self.assertEqual(pokemon_launcher.APP_NAME, "Pokémon PC Launcher")
        self.assertEqual(pokemon_launcher.APP_VERSION, "0.1")

    def test_game_package_and_activity_are_not_hardcoded_in_gui(self):
        self.assertNotIn("PKG_NAME", self.source)
        self.assertNotIn("UnityPlayerActivity", self.source)
        self.assertNotIn("jp.pokemon.pokemonchampions", self.source)

    def test_forced_process_exit_is_removed(self):
        self.assertNotIn("os._exit", self.source)
        self.assertNotIn("local_os._exit", self.source)

    def test_virtual_display_failure_does_not_fall_back_to_zero(self):
        self.assertNotIn('display_id = "0"', self.source)
        self.assertNotIn("Falling back to display ID", self.source)

    def test_existing_144_fps_option_is_preserved(self):
        self.assertIn("144", pokemon_launcher.FPS_VALUES)

    def test_game_switch_saves_settings_to_previous_profile(self):
        class Variable:
            def __init__(self, value):
                self.value = value

            def get(self):
                return self.value

        launcher = pokemon_launcher.AppLauncher.__new__(pokemon_launcher.AppLauncher)
        launcher.profiles = pokemon_launcher.load_game_profiles()
        launcher.current_profile_key = "pokemon_champions"
        launcher.config = {
            "game_resolutions": {
                "pokemon_champions": "1280x720",
                "pokemon_tcgpocket": "720x1280",
            },
            "custom_resolution_enabled": {
                "pokemon_champions": False,
                "pokemon_tcgpocket": False,
            },
            "custom_resolutions": {
                "pokemon_champions": {"width": "1280", "height": "720"},
                "pokemon_tcgpocket": {"width": "720", "height": "1280"},
            },
        }
        launcher.resolution_var = Variable("1920x1080")
        launcher.custom_enabled_var = Variable(True)
        launcher.custom_width_var = Variable("1600")
        launcher.custom_height_var = Variable("900")

        launcher._store_current_game_settings()

        self.assertEqual(
            launcher.config["game_resolutions"]["pokemon_champions"],
            "1920x1080",
        )
        self.assertEqual(
            launcher.config["game_resolutions"]["pokemon_tcgpocket"],
            "720x1280",
        )


if __name__ == "__main__":
    unittest.main()
