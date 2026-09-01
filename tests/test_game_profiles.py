# 공식 지원 게임 프로필의 데이터 계약을 검증한다.

import unittest

try:
    import game_profiles
except ImportError:
    game_profiles = None


class GameProfileTests(unittest.TestCase):
    def test_game_profiles_module_exists(self):
        self.assertIsNotNone(game_profiles)

    @unittest.skipIf(game_profiles is None, "game_profiles 모듈이 아직 없다.")
    def test_official_profiles_are_available(self):
        profiles = game_profiles.load_game_profiles()

        self.assertEqual(
            set(profiles),
            {"pokemon_champions", "pokemon_tcgpocket"},
        )

    @unittest.skipIf(game_profiles is None, "game_profiles 모듈이 아직 없다.")
    def test_champions_profile_preserves_existing_defaults(self):
        profile = game_profiles.load_game_profiles()["pokemon_champions"]

        self.assertEqual(profile.display_name, "Pokémon Champions")
        self.assertEqual(profile.package, "jp.pokemon.pokemonchampions")
        self.assertEqual(profile.orientation, "landscape")
        self.assertEqual(profile.default_resolution, "1280x720")
        self.assertEqual(profile.dpi, 320)
        self.assertIn("3840x2160", profile.resolutions)

    @unittest.skipIf(game_profiles is None, "game_profiles 모듈이 아직 없다.")
    def test_pocket_profile_uses_portrait_defaults(self):
        profile = game_profiles.load_game_profiles()["pokemon_tcgpocket"]

        self.assertEqual(profile.display_name, "Pokémon TCG Pocket")
        self.assertEqual(profile.package, "jp.pokemon.pokemontcgp")
        self.assertEqual(profile.orientation, "portrait")
        self.assertEqual(profile.default_resolution, "720x1280")
        self.assertIn("1440x2560", profile.resolutions)

    @unittest.skipIf(game_profiles is None, "game_profiles 모듈이 아직 없다.")
    def test_profiles_have_unique_packages_and_valid_defaults(self):
        profiles = game_profiles.load_game_profiles()

        self.assertEqual(len({profile.package for profile in profiles.values()}), 2)
        for key, profile in profiles.items():
            with self.subTest(key=key):
                self.assertEqual(profile.key, key)
                self.assertIn(profile.orientation, {"landscape", "portrait"})
                self.assertIn(profile.default_resolution, profile.resolutions)
                self.assertGreater(profile.dpi, 0)

    @unittest.skipIf(game_profiles is None, "game_profiles 모듈이 아직 없다.")
    def test_display_name_lookup_does_not_require_gui_logic(self):
        profile = game_profiles.get_profile_by_display_name("Pokémon TCG Pocket")

        self.assertEqual(profile.key, "pokemon_tcgpocket")


if __name__ == "__main__":
    unittest.main()
