# Pokémon PC Launcher 0.2 scrcpy 4.1 native 리팩터링 설계.

**작성일:** 2026-09-01.

**상태:** 승인됨.

## 목표.

- Pokémon PC Launcher를 scrcpy 4.1 기반의 얇은 GUI front-end로 정리한다.
- 게임 선택, 설정, 기기·package 확인, process/session 수명주기는 런처가 담당한다.
- Virtual Display 생성, 앱 force-stop·실행, display 정리, 화면 활성 유지는 scrcpy에 위임한다.
- 0.1 config와 ADB server ownership·graceful shutdown 동작을 보존한다.

## 책임 경계.

- `game_profiles.py`는 두 공식 게임의 package, 방향, 해상도와 DPI를 유지한다.
- `launcher_core.py`는 config, ADB 기기·package·Wi-Fi 서비스, scrcpy command builder와 process wrapper를 담당한다.
- `pokemon_launcher.py`는 Tkinter UI, 비동기 작업 조정, 버전 경고와 정상 종료를 담당한다.
- scrcpy 4.1은 `--new-display`, `--start-app=+PACKAGE`, `--keep-active`, `--flex-display`를 수행한다.

## 삭제 범위.

- Activity resolve/query/dumpsys 파서와 `am start-activity` 호출을 삭제한다.
- 직접 `am force-stop`, wake/keyguard 조작, `pidof`·activity polling을 삭제한다.
- Virtual Display ID 로그·`dumpsys display` 파서, 전후 차집합, 재시도와 `VirtualDisplayError`를 삭제한다.
- `ScrcpySession`은 stdout logging, wait, terminate·kill fallback, pipe close만 남긴다.

## scrcpy 실행 정책.

- 두 모드 모두 `-s SERIAL`, `--start-app=+PACKAGE`, `--keep-active`, `--stay-awake`, `--window-title`을 사용한다.
- `--keep-active`는 사용자 활동을 모사해 화면을 유지하고, 기존 `--stay-awake`는 충전 중 화면 유지 회귀를 막기 위해 함께 유지한다.
- Virtual Display는 `--new-display=WIDTHxHEIGHT/DPI`와 `--no-vd-system-decorations`를 사용한다.
- Mirror는 `--max-size=긴 변`을 사용한다.
- Flex Display는 Virtual Display에서만 `--flex-display`를 추가하며 기본값은 꺼짐이다.
- `--display-ime-policy=local`은 두 게임의 핵심 UX가 아니고 IME 동작을 바꿀 수 있으므로 기본 인자에 넣지 않는다.
- scrcpy 시작 후 짧은 구간에 process가 종료되면 exit code와 수집 로그를 사용자 오류로 보고한다. 실행 중 Android process polling은 하지 않는다.

## Wi-Fi 정책.

- v0.2에서는 기존 ADB 기반 사전 설정·수동 연결·상태 재검증·연결 해제를 유지한다.
- `scrcpy --tcpip`은 연결과 미러링 시작이 결합되어 현재의 사전 연결·기기 선택·종료 시 연결 해제 UX와 맞지 않는다.
- native TCP/IP 전환은 연결 방식 UI와 ADB ownership 정책을 함께 재설계하는 후속 작업으로 분리한다.

## 번들·버전 정책.

- 공식 `scrcpy-win64-v4.1.zip`의 SHA-256 `5b12172b3264b2889f4583ee64752ce832e29bc8b1089dca81093459697165db`를 검증한다.
- 공식 ZIP 내용을 `bin/scrcpy/`에 보존하고 bundled ADB도 같은 디렉터리에서 사용한다.
- 중복된 `bin/adb/`는 제거해 scrcpy와 ADB의 버전·DLL 구성을 하나의 공식 단위로 유지한다.
- 시작 시 `scrcpy --version`을 실행해 4.1이면 로그만 남기고, 다른 버전·탐지 실패면 GUI에 경고한다.

## 설정과 GUI.

- 앱 버전을 0.2로 올린다.
- `flex_display`를 기본 `false`로 config에 추가하고 0.1 config에 키가 없어도 정상 보정한다.
- 화면 설정에 `창 크기에 자동 맞춤 (Flex Display)` 체크를 추가하고 Mirror 선택 시 적용되지 않음을 UI 상태로 표현한다.
- FPS 라벨을 `최대 전송 FPS`로 바꾸고 게임 자체 FPS를 높이는 기능이 아님을 README에 설명한다.

## 오류·종료·검증.

- package 설치 여부는 scrcpy 시작 전에 계속 검사한다.
- `ScrcpySession`은 정상 exit, 조기 오류 exit, terminate, kill fallback과 pipe close를 검증한다.
- 런처 종료 순서와 `AdbServerManager` 소유권 판정은 유지한다.
- 실제 Android 게임 렌더링, Flex resize와 Wi-Fi 조합은 자동 테스트 성공과 구분해 수동 확인 항목으로 남긴다.

## 완료 조건.

- 공식 scrcpy 4.1 번들과 실제 dependency 고지가 일치한다.
- Activity·display ID·force-stop·app-running 자체 구현과 관련 테스트가 실제로 삭제된다.
- command builder, config migration, version 검사, session·ADB lifecycle 테스트가 통과한다.
- 새 EXE가 소스와 일치하고 Windows 종료 뒤 관련 process와 폴더 잠금이 남지 않는다.
