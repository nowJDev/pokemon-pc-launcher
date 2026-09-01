# Pokémon PC Launcher 0.1 구현 계획.

> **For agentic workers: REQUIRED SUB-SKILL:** `executing-plans`를 사용하며 모든 단계는 아래 체크박스와 증거를 따른다.

**목표:** Champions 기존 기능을 보존하면서 프로필 기반 TCG Pocket 지원과 검증 가능한 ADB·scrcpy 실행 흐름을 구현한다.

**아키텍처:** 게임 데이터는 `game_profiles.py`, 장치·명령·파서는 `launcher_core.py`, UI는 `pokemon_launcher.py`로 분리한다.

**기술 스택:** Python 3.11 표준 라이브러리, Tkinter, `unittest`, ADB 37.0.0, scrcpy 4.0, PyInstaller 6.20.0.
**설계 문서:** `docs/superpowers/specs/2026-09-01-multigame-launcher-design.md`.

## 파일 구조.

- 생성 `game_profiles.py`: 프로필 데이터와 유효성 검사다.
- 생성 `launcher_core.py`: 순수 파서, 설정, 명령 실행, ADB와 scrcpy 서비스다.
- 수정 `pokemon_launcher.py`: Tkinter GUI와 백그라운드 작업 조정이다.
- 생성 `tests/test_game_profiles.py`: 프로필 테스트다.
- 생성 `tests/test_launcher_core.py`: 파서·설정·인자 테스트다.
- 수정 `README.md`: 0.1 사용법, 두 게임과 보안 안내다.
- 생성 `THIRD_PARTY_NOTICES.md`: 포함 바이너리와 확인한 upstream 고지다.
- 수정 `.gitignore`: 런타임 로그·설정 제외다.
- 교체 루트 실행 파일: `Pokémon Champions.exe`를 제거하고 `Pokémon PC Launcher.exe`를 생성한다.

### Task 1. 게임 프로필과 해상도 계약.

**영향 파일.**

- 생성: `game_profiles.py`.
- 생성: `tests/test_game_profiles.py`.
- 테스트: `tests/test_game_profiles.py`.

**구현·검증 체크리스트.**

- [ ] 다음 계약의 테스트를 먼저 작성한다.

```python
def test_official_profiles_have_unique_packages_and_valid_defaults(self):
    profiles = load_game_profiles()
    self.assertEqual(set(profiles), {"pokemon_champions", "pokemon_tcgpocket"})
    self.assertEqual(len({p.package for p in profiles.values()}), 2)
    for profile in profiles.values():
        self.assertIn(profile.default_resolution, profile.resolutions)
        self.assertIn(profile.orientation, {"landscape", "portrait"})
```

- [ ] `python -m unittest tests.test_game_profiles -v`를 실행해 모듈 부재 실패를 확인한다.
- [ ] `GameProfile`, `GAME_PROFILES`, `load_game_profiles()`와 프로필 검증을 최소 구현한다.
- [ ] Champions는 `1280x720`, Pocket은 `720x1280`, 두 프로필 DPI는 320으로 설정한다.
- [ ] 대상 테스트를 다시 실행해 통과를 확인한다.

### Task 2. 순수 파서, 해상도와 설정 마이그레이션.

**영향 파일.**

- 생성: `launcher_core.py`.
- 생성: `tests/test_launcher_core.py`.
- 테스트: `tests/test_launcher_core.py`.

**구현·검증 체크리스트.**

- [ ] 다음 입력 계약을 각각 독립 테스트로 작성한다.

```python
ADB_SAMPLE = """List of devices attached
USB123 device product:x model:Phone
USB456 unauthorized
192.168.0.8:5555 offline
"""

def test_parse_adb_devices_preserves_state(self):
    devices = parse_adb_devices(ADB_SAMPLE)
    self.assertEqual([(d.serial, d.state) for d in devices], [
        ("USB123", "device"),
        ("USB456", "unauthorized"),
        ("192.168.0.8:5555", "offline"),
    ])

def test_rfc1918_filter_rejects_non_private_172_and_link_local(self):
    self.assertTrue(is_wifi_candidate_ip("172.16.0.1"))
    self.assertFalse(is_wifi_candidate_ip("172.15.0.1"))
    self.assertFalse(is_wifi_candidate_ip("169.254.1.2"))

def test_legacy_config_migrates_to_champions(self):
    loaded = normalize_config({"resolution": "1920x1080", "custom_width": "1600", "custom_height": "900"})
    self.assertEqual(loaded["game_resolutions"]["pokemon_champions"], "1920x1080")
    self.assertEqual(loaded["custom_resolutions"]["pokemon_champions"], {"width": "1600", "height": "900"})
```

- [ ] package 목록, resolve Activity, dumpsys Activity, scrcpy 로그와 dumpsys display 표본 테스트를 추가한다.
- [ ] 사용자 해상도 320~7680 범위와 orientation 불일치 경고 테스트를 추가한다.
- [ ] `python -m unittest tests.test_launcher_core -v`로 예상 실패를 확인한다.
- [ ] `AdbDevice`, `CommandResult`, 파서 함수, `normalize_config()`, 원자적 config 저장과 `build_scrcpy_args()`를 구현한다.
- [ ] 대상 테스트와 전체 테스트를 실행한다.

### Task 3. 명령 실행과 ADB 서비스.

**영향 파일.**

- 수정: `launcher_core.py`.
- 수정: `tests/test_launcher_core.py`.
- 테스트: `tests/test_launcher_core.py`.

**구현·검증 체크리스트.**

- [ ] 주입한 runner 결과로 `device`, `offline`, `unauthorized`가 분리되는 테스트를 작성한다.
- [ ] 수동·자동 Wi-Fi 연결이 `adb connect` 뒤 endpoint의 `state == "device"`를 재시도 검증하는 테스트를 작성한다.
- [ ] Activity 탐색이 resolve 명령, query fallback, dumpsys fallback 순서로 동작하고 실패 시 빈 값을 반환하는 테스트를 작성한다.
- [ ] `run_command(args, timeout)`이 `TimeoutExpired`를 `timed_out=True`로 반환하는 테스트를 작성한다.
- [ ] `python -m unittest tests.test_launcher_core -v`에서 새 테스트의 예상 실패를 확인한다.
- [ ] `AdbService`의 devices, package, activity, IP, tcpip, connect, disconnect, launch와 app-running 검증을 구현한다.
- [ ] 포트 5037 사전 상태와 `server-status` 실행 경로로 bundled ADB server 소유권을 판정하는 테스트를 작성한다.
- [ ] 런처 소유 서버는 자동 종료하고 pre-existing server는 기본 보존하며 명시적 강제 옵션만 허용하는 `AdbServerManager`를 구현한다.
- [ ] 모든 ADB 명령에 용도별 timeout과 오류 로그를 지정하고 대상 테스트를 통과시킨다.

### Task 4. scrcpy와 Virtual Display 수명주기.

**영향 파일.**

- 수정: `launcher_core.py`.
- 수정: `tests/test_launcher_core.py`.
- 테스트: `tests/test_launcher_core.py`.

**구현·검증 체크리스트.**

- [ ] Virtual Display 인자에 `--new-display=해상도/DPI`가 있고 미러링 인자에는 없는 테스트를 작성한다.
- [ ] FPS, 화면 끄기, borderless fullscreen, stay awake와 프로필 제목 인자 테스트를 작성한다.
- [ ] 기존 display 집합과 새 dumpsys 집합의 차이만 선택하며 0을 거부하는 테스트를 작성한다.
- [ ] display 탐지 실패 시 `VirtualDisplayError`가 발생하는 테스트를 작성한다.
- [ ] 테스트 실패를 확인한 뒤 `ScrcpyService`의 프로세스 시작, 비차단 로그 drain, display 재시도와 terminate/wait/kill 정리를 구현한다.
- [ ] 대상 테스트와 전체 테스트를 통과시킨다.

### Task 5. Tkinter 멀티게임 GUI 통합.

**영향 파일.**

- 수정: `pokemon_launcher.py`.
- 테스트: `tests/test_game_profiles.py`, `tests/test_launcher_core.py`.

**구현·검증 체크리스트.**

- [ ] 실행 전 검증 순서를 호출하는 순수 요청 생성 함수 테스트를 작성한다.
- [ ] GUI 최상단에 게임 선택, 화면 설정에 명시적 실행 모드, 무선 연결 영역에 해제 버튼을 추가한다.
- [ ] 게임 변경 시 프로필 해상도·기본값·window title·실행 버튼·orientation 안내를 갱신한다.
- [ ] 기기 목록에 상태를 표시하고 실행 가능 상태를 `device`로 제한한다.
- [ ] 패키지 설치와 Activity를 scrcpy 실행 전에 확인한다.
- [ ] 모든 백그라운드 결과의 위젯 변경을 `root.after()` 콜백으로 전달한다.
- [ ] `os._exit(0)`을 제거하고 활성 scrcpy 종료, logger shutdown, `root.destroy()` 순서의 정상 종료를 구현한다.
- [ ] scrcpy 종료 확인, pipe close, worker join, 무선 endpoint disconnect, config 저장, ADB server 정책 적용, 로그 flush, root destroy 순서를 `finally` 경로로 보장한다.
- [ ] 기존 ADB server 강제 종료 체크박스는 기본 해제하고 공유 도구 영향 경고를 표시한다.
- [ ] `python -c "import pokemon_launcher; print(pokemon_launcher.APP_VERSION)"`가 `0.1`을 출력하는지 확인한다.

### Task 6. 문서, 고지와 배포 실행 파일.

**영향 파일.**

- 수정: `README.md`, `.gitignore`.
- 생성: `THIRD_PARTY_NOTICES.md`.
- 교체: 루트 Windows 실행 파일.

**구현·검증 체크리스트.**

- [ ] README의 한글·영문 안내를 Pokémon PC Launcher 0.1과 두 게임·두 실행 모드 기준으로 갱신한다.
- [ ] 게임 미포함, 비공식 프로젝트, 공용 Wi-Fi 무선 ADB 위험과 연결 해제 절차를 명시한다.
- [ ] ADB, scrcpy, SDL, FFmpeg와 libusb의 포함 버전·공식 upstream·검증 한계를 고지한다.
- [ ] `config.json`, `launcher.log`, `ip_debug.log`를 Git 제외 목록에 추가한다.
- [ ] PyInstaller `--onefile --windowed --icon` 빌드로 `Pokémon PC Launcher.exe`를 생성한다.
- [ ] 기존 Champions 전용 실행 파일을 제거하고 새 실행 파일의 시작·종료를 제한 시간 내 확인한다.

### Task 7. 전체 검증, 리뷰와 커밋.

**영향 파일.**

- 수정: `docs/design-progress-checklist.md`, `docs/current-state.md`.
- 생성: `docs/reviews/2026-09-01-multigame-launcher-review.md`.
- 테스트: 전체 변경 파일.

**구현·검증 체크리스트.**

- [ ] `python -m unittest discover -v` 전체 결과를 기록한다.
- [ ] 모든 Python 파일 AST·compileall 검사와 PyInstaller 빌드를 실행한다.
- [ ] 코드 리뷰에서 정확성, 단순성, 보안, 프로세스 정리와 문서 정합성을 확인한다.
- [ ] `git diff --check`, `git status`, 빌드 산출물과 시크릿 누락을 확인한다.
- [ ] 실제 장치가 필요한 16개 시나리오는 수동 검증 대기로 표시한다.
- [ ] Windows에서 정상 종료 후 관련 프로세스 부재와 프로그램 폴더 rename·삭제 가능 여부를 확인한다.
- [ ] 코드·테스트·문서·실행 파일을 하나의 0.1 논리 변경으로 한글 커밋한다.

## 최종 통합.

- [ ] 전체 빌드·테스트·정적 검사가 통과한다.
- [ ] 코드 리뷰의 필수 지적을 해결한다.
- [ ] 현재 상태 문서가 실제 상태와 일치한다.
- [ ] 기능 브랜치 커밋을 완료하고 병합·푸시는 별도 승인 전 수행하지 않는다.
