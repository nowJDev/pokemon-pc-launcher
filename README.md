# Pokémon PC Launcher

**ADB와 scrcpy로 Pokémon Champions와 Pokémon TCG Pocket을 PC에서 실행하는 비공식 Windows 런처입니다.**

Android 기기에 설치된 게임을 PC의 독립 창 또는 기본 화면 미러링으로 실행합니다.

> **개발 상태:** 현재 버전은 기능 안정화 단계인 **0.1**입니다. 실제 기기 조합에서 주요 시나리오를 모두 검증한 뒤에만 1.0으로 올릴 예정입니다.

이 저장소에는 Pokémon 게임 자체가 포함되어 있지 않습니다. 사용자가 소유한 Android 기기에 게임을 직접 설치해야 합니다.

## 공식 지원 게임

| 게임 | 화면 방향 | 기본 해상도 | 권장 실행 방식 |
| --- | --- | --- | --- |
| Pokémon Champions | 가로 | 1280x720 | Virtual Display |
| Pokémon TCG Pocket | 세로 | 720x1280 | Virtual Display 또는 기본 화면 미러링 |

Pokémon TCG Pocket의 Virtual Display 호환성은 기기와 Android 버전에 따라 다를 수 있습니다. 화면이 정상적으로 렌더링되지 않으면 실행 모드를 `기본 화면 미러링`으로 직접 바꾸세요. 런처는 예상하지 못한 화면 전환을 막기 위해 자동 fallback을 수행하지 않습니다.

## 주요 기능

- 게임 프로필 기반 멀티게임 선택.
- USB 및 Wi-Fi ADB 기기 선택과 상태 표시.
- USB 기기의 TCP/IP 5555 자동 설정과 연결 상태 재검증.
- 수동 무선 ADB 연결 및 연결 해제.
- 게임별 기본 해상도, 사용자 지정 해상도, 기기 원본 해상도.
- FPS 제한, Borderless Fullscreen, 스마트폰 화면 끄기, stay-awake.
- Virtual Display 생성 후 실제 display ID 탐색과 선택 게임 자동 실행.
- 기본 Android display 0을 사용하는 명시적 미러링 호환 모드.
- Package 설치 여부와 launchable Activity 자동 탐색.
- 종료 시 scrcpy, pipe, worker, 런처가 생성한 무선 연결과 ADB server 정리.

## 실행 전 준비

1. Windows 10 이상 PC를 사용합니다.
2. Android 기기에서 `설정 → 휴대전화 정보 → 소프트웨어 정보 → 빌드 번호`를 여러 번 눌러 개발자 옵션을 활성화합니다.
3. 개발자 옵션에서 `USB 디버깅`을 켭니다.
4. USB 케이블로 기기를 연결하고 스마트폰에 표시되는 디버깅 허용 창을 승인합니다.
5. 지원 게임을 Android 기기에 설치합니다.

`unauthorized` 상태가 표시되면 스마트폰에서 USB 디버깅 허용을 승인하세요. `offline` 상태가 표시되면 케이블 또는 무선 연결을 다시 연결한 뒤 기기 목록을 새로고침하세요.

## 사용 방법

1. `Pokémon PC Launcher.exe` 또는 `python pokemon_launcher.py`를 실행합니다.
2. 실행할 게임을 선택합니다.
3. 연결할 Android 기기를 선택합니다.
4. 필요하면 USB 기기를 무선 ADB로 자동 설정하거나 IP 주소로 연결합니다.
5. 해상도와 실행 모드, FPS 및 화면 옵션을 선택합니다.
6. 게임 실행 버튼을 누릅니다.

게임 실행 전 런처는 다음 순서로 검증합니다.

1. 선택 게임과 기기.
2. 기기의 현재 ADB 상태.
3. 선택 게임 package의 정확한 설치 여부.
4. Android Package Manager가 반환하는 launchable Activity.
5. 해상도와 실행 옵션.
6. scrcpy 실행과 Virtual Display ID.
7. Activity 실행과 게임 프로세스 상태.

어느 단계에서든 실패하면 다음 단계로 넘어가지 않으며 `launcher.log`에 진단 내용을 남깁니다.

## 실행 모드

### Virtual Display

scrcpy의 `--new-display=WIDTHxHEIGHT/DPI`로 새 Android display를 만든 뒤, scrcpy 로그와 `dumpsys display`를 이용해 새 display ID를 확인합니다. ID를 찾지 못하면 display 0으로 전환하지 않고 오류로 종료합니다.

### 기본 화면 미러링

선택한 앱을 Android 기본 display 0에서 실행하고 일반 scrcpy 미러링을 사용합니다. 선택 해상도의 긴 변은 scrcpy `--max-size`에 적용됩니다. Virtual Display에서 렌더링되지 않는 게임이나 기기의 호환 모드입니다.

## 무선 ADB 보안

기존 방식과의 호환성을 위해 TCP/IP 5555를 사용합니다. 같은 네트워크의 다른 장치가 접근할 가능성이 있으므로 신뢰할 수 있는 개인 Wi-Fi에서만 사용하세요.

- 사용 후 런처의 `연결 해제` 버튼을 누르세요.
- 공용 Wi-Fi에서는 무선 ADB를 켜 두지 마세요.
- 가능하면 USB를 다시 연결한 뒤 `adb usb`로 TCP 모드를 종료하세요.

## 종료 및 ADB server 정책

런처가 현재 bundled `adb.exe`로 새 ADB server를 시작한 것이 확인되면 정상 종료 과정에서 그 server를 자동으로 종료합니다. 실행 전부터 존재하던 ADB server는 Android Studio나 Unity가 공유할 수 있으므로 기본적으로 유지합니다.

`종료 시 기존 ADB 서버도 종료 (고급)`을 선택하면 기존 server에도 `adb kill-server`를 실행합니다. 다른 Android 개발 도구의 연결도 끊길 수 있으므로 필요한 경우에만 사용하세요.

정상 종료 순서는 scrcpy 종료와 pipe 닫기, worker 정리, 런처가 만든 무선 연결 해제, 설정 저장, ADB server 정책 적용, 로그 flush, Tkinter 종료 순입니다. 강제 종료인 `os._exit()`은 사용하지 않습니다.

## 설정과 로그

- `config.json`은 마지막 게임, 실행 모드, 게임별 해상도, 사용자 지정 해상도, FPS와 화면 옵션, 무선 IP를 저장합니다.
- 이전 Champions 전용 `config.json`도 자동으로 새 구조에 병합합니다.
- `launcher.log`는 ADB, IP 탐색, Activity, display ID, 게임 실행과 종료 결과를 기록합니다.

이 파일들은 실행 중 생성되며 Git에는 포함하지 않습니다.

## 개발 및 테스트

Python 3.10 이상을 권장합니다. 런타임 코드는 Python 표준 라이브러리만 사용합니다.

```powershell
python -m unittest discover -v
python pokemon_launcher.py
```

Android 기기가 필요 없는 테스트는 프로필, ADB 출력 파싱, Activity와 display ID 파싱, RFC1918 IP 판별, 해상도, 설정 마이그레이션, scrcpy 인자와 process 수명주기를 검증합니다.

실제 기기에서는 Champions와 TCG Pocket 각각 USB·Wi-Fi·Virtual Display·기본 미러링 조합을 확인해야 합니다. 종료 후 작업 관리자에서 런처, scrcpy, 불필요한 bundled ADB process가 남지 않는지와 프로그램 폴더의 이름 변경 및 삭제 가능 여부도 확인해야 합니다.

## 새 게임 프로필 추가

공식 지원 대상을 늘릴 때는 `game_profiles.py`에 package, 화면 방향, 기본 해상도, 해상도 목록과 DPI를 추가합니다. Activity 이름은 프로필에 넣지 않습니다. 런처가 Android Package Manager에서 실제 launchable Activity를 탐색합니다.

## 제3자 구성요소와 라이선스

저장소의 바이너리 구성과 확인 상태는 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)를 참조하세요. 확인된 원문 라이선스와 NOTICE는 [licenses](licenses/)에 포함되어 있습니다. 공개 바이너리 Release는 원본 코드 재배포 조건과 FFmpeg 대응 소스 제공 절차가 확정된 뒤에만 만듭니다.

## 비공식 프로젝트 고지

이 프로젝트는 Nintendo, The Pokémon Company, Creatures Inc., GAME FREAK inc. 또는 각 게임 개발·배급사와 제휴하거나 승인받은 프로젝트가 아닙니다. Pokémon 및 관련 명칭과 표장은 각 권리자의 상표입니다.

---

## English summary

Pokémon PC Launcher 0.1 is an unofficial Windows launcher that controls ADB and scrcpy to display games already installed on the user's Android device. It currently supports Pokémon Champions and Pokémon TCG Pocket profiles. No game files are included.

Choose Virtual Display for an independent Android display or Basic Screen Mirroring for compatibility. The launcher resolves the real launchable Activity from Android Package Manager and never guesses an Activity name. A Virtual Display detection failure is reported instead of silently launching on display 0.

Wireless ADB uses TCP port 5555. Use it only on trusted networks and disconnect it after use. Version 1.0 is reserved for completion of real-device stabilization tests.
