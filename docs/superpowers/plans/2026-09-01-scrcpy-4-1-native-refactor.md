# Pokémon PC Launcher 0.2 scrcpy 4.1 native 리팩터링 계획.

**목표:** 0.1의 런처 고유 기능을 보존하면서 Android 내부 실행·Virtual Display 제어를 scrcpy 4.1 native 옵션으로 치환한다.

**설계 문서:** `docs/superpowers/specs/2026-09-01-scrcpy-4-1-native-refactor-design.md`.

## Task 1. 기준선과 공식 번들 검증.

**영향 파일:** `bin/`, `licenses/`, `THIRD_PARTY_NOTICES.md`.

- [x] 현재 전체 테스트와 line count를 기록한다.
- [x] 공식 v4.1 ZIP의 게시 SHA-256을 검증한다.
- [x] 공식 ZIP 파일 목록·버전·dependency를 수집하고 기존 번들과 비교한다.
- [x] `bin/scrcpy/`를 공식 ZIP 구조로 교체하고 중복 `bin/adb/`를 제거한다.

## Task 2. command builder와 config를 테스트 우선으로 변경.

**영향 파일:** `tests/test_launcher_core.py`, `launcher_core.py`.

- [x] Champions·Pocket의 Virtual·Mirror command 기대값, Flex, keep-active와 start-app 테스트를 먼저 실패시킨다.
- [x] 0.1 config의 `flex_display=False` migration 테스트를 먼저 실패시킨다.
- [x] `ScrcpyOptions`와 `build_scrcpy_args()`를 최소 변경해 테스트를 통과시킨다.
- [x] 통합 번들의 ADB 경로 우선순위 테스트를 추가한다.

## Task 3. 중복 Android 제어를 삭제.

**영향 파일:** `tests/test_launcher_core.py`, `launcher_core.py`, `tests/test_launcher_gui.py`, `pokemon_launcher.py`.

- [x] 삭제 대상 심볼과 금지 명령이 없는 계약 테스트를 먼저 추가한다.
- [x] Activity resolve·launch, force-stop, wake·unlock, app polling, display ID 파서·서비스·예외를 삭제한다.
- [x] GUI launch flow를 package 확인→command build→scrcpy session 시작으로 단순화한다.

## Task 4. ScrcpySession과 버전 검사를 테스트 우선으로 정리.

**영향 파일:** `tests/test_launcher_core.py`, `launcher_core.py`, `pokemon_launcher.py`.

- [x] 4.1 version parsing·불일치와 조기 종료 결과 테스트를 먼저 실패시킨다.
- [x] `ScrcpySession`에 process 상태·로그 snapshot·bounded startup 확인만 남긴다.
- [x] 시작 시 정상 4.1은 로그만 남기고 불일치는 main thread에서 경고한다.

## Task 5. Flex Display와 v0.2 GUI를 통합.

**영향 파일:** `tests/test_launcher_gui.py`, `pokemon_launcher.py`, `launcher_core.py`.

- [x] `APP_VERSION=0.2`, flex config 저장과 GUI 변수 계약 테스트를 먼저 실패시킨다.
- [x] 화면 설정에 기본 OFF Flex checkbox를 추가하고 Virtual mode에서만 활성화한다.
- [x] FPS 문구를 `최대 전송 FPS`로 바꾸고 기존 옵션을 보존한다.

## Task 6. 문서와 라이선스를 실제 번들에 맞춘다.

**영향 파일:** `README.md`, `THIRD_PARTY_NOTICES.md`, `licenses/`, `docs/current-state.md`, `docs/design-progress-checklist.md`.

- [x] README의 Activity·display ID 설명을 scrcpy native 위임 설명으로 교체한다.
- [x] scrcpy 4.1, FFmpeg 8.1.2, SDL 3.4.12, libusb 1.0.30과 실제 ADB 정보를 반영한다.
- [x] upstream 원문과 실제 정적 의존성 버전을 확인해 `licenses/`를 교체한다.
- [x] Wi-Fi 유지 결정, Flex 실기기 제한과 배포 게이트를 문서화한다.

## Task 7. 전체 검증과 EXE 재빌드.

**영향 파일:** 전체 변경, `Pokémon PC Launcher.exe`.

- [x] 전체 unittest, compileall, 금지 문자열 검색과 `git diff --check`를 통과시킨다.
- [x] 코드 리뷰에서 정확성·단순성·프로세스 종료·문서 정합성을 확인한다.
- [x] PyInstaller onefile/windowed EXE를 마지막에 재빌드한다.
- [x] EXE GUI 시작·WM_CLOSE 뒤 launcher·scrcpy·bundled ADB 잔존 0과 임시 폴더 rename·delete를 확인한다.
- [x] line count 전후와 실제 기기 TODO를 최종 보고에 기록한다.

## Task 8. 통합.

- [ ] 한글 논리 커밋을 만들고 `main`에 fast-forward 병합한다.
- [ ] 원격 `main`에 push한 뒤 원격 SHA를 확인한다.
- [ ] 현재 상태를 handover 문서에 기록한다.
