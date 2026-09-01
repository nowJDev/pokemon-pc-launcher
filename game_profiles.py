# 공식 지원 게임의 실행 프로필과 유효성 검사를 제공한다.

from dataclasses import dataclass


@dataclass(frozen=True)
class GameProfile:
    key: str
    display_name: str
    package: str
    orientation: str
    default_resolution: str
    resolutions: tuple[str, ...]
    dpi: int = 320


GAME_PROFILES = {
    "pokemon_champions": GameProfile(
        key="pokemon_champions",
        display_name="Pokémon Champions",
        package="jp.pokemon.pokemonchampions",
        orientation="landscape",
        default_resolution="1280x720",
        resolutions=(
            "3840x2160",
            "2560x1440",
            "1920x1080",
            "1600x900",
            "1280x720",
            "960x540",
        ),
    ),
    "pokemon_tcgpocket": GameProfile(
        key="pokemon_tcgpocket",
        display_name="Pokémon TCG Pocket",
        package="jp.pokemon.pokemontcgp",
        orientation="portrait",
        default_resolution="720x1280",
        resolutions=(
            "2160x3840",
            "1440x2560",
            "1080x1920",
            "900x1600",
            "720x1280",
            "540x960",
        ),
    ),
}


def _validate_profiles(profiles):
    packages = set()
    display_names = set()
    for key, profile in profiles.items():
        if profile.key != key:
            raise ValueError(f"프로필 키가 일치하지 않습니다: {key}")
        if profile.orientation not in {"landscape", "portrait"}:
            raise ValueError(f"지원하지 않는 화면 방향입니다: {profile.orientation}")
        if profile.default_resolution not in profile.resolutions:
            raise ValueError(f"기본 해상도가 목록에 없습니다: {key}")
        if profile.dpi <= 0:
            raise ValueError(f"DPI는 양수여야 합니다: {key}")
        if profile.package in packages:
            raise ValueError(f"중복 package입니다: {profile.package}")
        if profile.display_name in display_names:
            raise ValueError(f"중복 게임 이름입니다: {profile.display_name}")
        packages.add(profile.package)
        display_names.add(profile.display_name)


def load_game_profiles():
    _validate_profiles(GAME_PROFILES)
    return dict(GAME_PROFILES)


def get_profile_by_display_name(display_name):
    for profile in load_game_profiles().values():
        if profile.display_name == display_name:
            return profile
    raise KeyError(display_name)
