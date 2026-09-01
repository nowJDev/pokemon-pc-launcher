# Pokémon PC Launcher 0.1 설계 명세.

**작성일:** 2026-09-01.

**상태:** 승인됨.
**담당자:** Codex 구현 에이전트.

## 목표.

- Pokémon Champions와 Pokémon TCG Pocket을 지원하는 Windows용 Android 게임 런처를 제공한다.
- 새 게임은 프로필 항목만 추가해 GUI, ADB, scrcpy 실행 흐름을 재사용할 수 있게 한다.
- 기존 Champions의 USB·Wi-Fi ADB, Virtual Display, FPS, 전체화면, 화면 끄기, 해상도, 아이콘 기능을 보존한다.
- ADB 상태, 패키지, Activity, Virtual Display를 검증한 뒤에만 다음 실행 단계로 진행한다.

## 비목표.

- Android 게임 APK 또는 게임 데이터를 배포하지 않는다.
- Virtual Display 실패 시 기본 화면으로 자동 전환하지 않는다.
- 이번 릴리스에서 두 공식 지원 게임 외의 게임 호환성을 보장하지 않는다.
- 실제 Android 제조사별 동작을 자동 테스트만으로 검증했다고 주장하지 않는다.
- 포함 바이너리의 법률적 라이선스 적합성을 단정하지 않는다.

## 기준선.

- 현재 동작: `AppLauncher` 단일 클래스가 Champions 전용 GUI, 설정, ADB, IP 탐색, scrcpy와 프로세스 종료를 담당한다.
- 관련 파일·시스템: `pokemon_launcher.py`, `README.md`, `bin/adb`, `bin/scrcpy`, 루트 PyInstaller 실행 파일이다.
- 제약 조건: Python 3.11과 Tkinter, Windows, ADB 37.0.0, scrcpy 4.0을 사용하며 외부 Python 패키지를 추가하지 않는다.
- 기존 결함: 패키지·Activity·DPI·제목 하드코딩, 5초 고정 timeout, ADB 상태 미구분, 무선 연결 미검증, display 0 fallback, 무음 예외와 `os._exit(0)`이 있다.

## 사용자·시스템 흐름.

1. 사용자는 게임, Android 기기, 연결 방식, 실행 모드, 해상도와 화면 옵션을 선택한다.
2. 런처는 실행 파일 존재, 기기 상태, 패키지 설치, launch Activity와 해상도를 순서대로 검증한다.
3. Virtual Display 모드는 scrcpy가 만든 새 display ID를 로그와 `dumpsys display`에서 확인한 후 해당 display에서 Activity를 실행한다.
4. 기본 화면 미러링 모드는 새 display를 만들지 않고 display 0에서 Activity를 실행하며 scrcpy 기본 미러링을 사용한다.
5. 실패하면 이후 단계를 중단하고 scrcpy를 정리한 뒤 GUI를 복원해 이해 가능한 오류를 표시한다.
6. scrcpy 창이 닫히거나 런처 종료가 요청되면 scrcpy, pipe, worker, 무선 연결, config, 로그, Tkinter 순서로 정리한다.
7. 시작 전 ADB server가 없었고 시작 후 실행 경로가 bundled ADB와 일치하면 런처가 소유한 서버로 기록해 종료 시 정리한다.

## 아키텍처와 책임 경계.

- `game_profiles.py`: `GameProfile`과 두 공식 게임 프로필, 프로필 유효성 검사를 담당한다.
- `launcher_core.py`: 명령 실행, 순수 파서, 설정 마이그레이션, ADB 서비스, scrcpy 인자·프로세스와 Virtual Display 탐지를 담당한다.
- `pokemon_launcher.py`: Tkinter 위젯, 백그라운드 작업 조정, 사용자 메시지와 정상 종료를 담당한다.
- `tests/`: 실제 장치 없이 프로필, 파서, 설정, 검증과 인자 생성을 검사한다.
- 외부 연동: 로컬 `adb.exe`, `scrcpy.exe`, 선택한 Android 기기만 사용한다.

## 데이터와 생명주기.

- 입력: 게임 키, ADB serial, 실행 모드, 해상도, FPS와 화면 옵션이며 신뢰 경계에서 검증한다.
- 상태: `config.json`에 마지막 게임·모드·게임별 해상도·사용자 해상도·FPS·화면 옵션·무선 IP·기존 ADB server 강제 종료 선택을 저장한다.
- 호환성: 기존 `resolution`, `custom_width`, `custom_height` 키는 Champions 설정으로 마이그레이션한다.
- 출력: scrcpy 명령 인자, Activity 시작 결과, 상태 메시지와 `launcher.log`다.
- 생성·갱신·폐기 시점: GUI 시작 시 설정을 읽고 선택 변경·실행 시 저장하며, 로그 핸들러와 자식 프로세스는 종료 시 정리한다.

## 오류·복구·관측성.

- 예상 오류: 바이너리 누락, unauthorized/offline 기기, 패키지 미설치, Activity 탐색 실패, timeout, Wi-Fi 연결 검증 실패, display 탐지 실패와 Activity 시작 실패다.
- 복구 전략: 무선 연결과 display 탐지는 제한 횟수 재시도하고, 실패 시 성공을 표시하지 않으며 사용자 재시도를 허용한다.
- Virtual Display 실패: display 0으로 전환하지 않고 생성한 scrcpy 프로세스를 종료한다.
- 로그·메트릭: 앱 시작, 프로필, package, 기기 상태, IP 후보, display ID, Activity, 명령 실패·timeout, scrcpy·pipe·worker·ADB server 종료 결과와 종료 sequence 완료를 `launcher.log`에 기록한다.
- 개인정보: 명령 전체 환경, Wi-Fi SSID, 인증 정보와 장치 속성 전체를 기록하지 않는다.

## 검증 전략.

- 자동 테스트: `python -m unittest discover -v`로 IP, ADB devices, package, Activity, display, 해상도, 프로필, config와 scrcpy 인자를 검사한다.
- 정적 검사: 모든 Python 파일 AST 구문 검사와 `python -m compileall -q`를 실행한다.
- 빌드: PyInstaller로 `Pokémon PC Launcher.exe`를 만들고 제한 시간 내 시작·종료를 확인한다.
- 수동 검증: 두 게임의 USB·Wi-Fi, Virtual Display·미러링, 미설치, unauthorized, offline과 연결 해제를 실제 Android 기기에서 확인한다.
- 회귀 범위: Champions의 기존 해상도, FPS, borderless, 화면 끄기, stay awake, 기기 해상도와 아이콘을 포함한다.

## 보안·개인정보·배포.

- 무선 ADB는 TCP 5555를 유지하되 연결 성공을 `adb devices` 상태로 검증하고 종료 기능과 공용 Wi-Fi 경고를 제공한다.
- 포트 5037이 시작 전 열려 있으면 Android Studio·Unity 등 외부 도구가 공유하는 서버로 간주해 기본 종료 대상에서 제외한다.
- 시작 전 서버가 없고 `server-status`의 실행 경로가 bundled ADB와 일치할 때만 자동 `kill-server`한다.
- 사용자가 기존 서버 종료 옵션을 명시적으로 선택한 경우에만 pre-existing server도 종료하며 GUI에서 다른 Android 도구 영향 가능성을 알린다.
- 로컬 번들 바이너리를 우선하며 `C:\\scrcpy` 같은 사용자 PC 고정 경로 의존성을 제거한다.
- `config.json`과 `launcher.log`는 Git 추적에서 제외한다.
- PyInstaller 결과는 기존 Champions 전용 실행 파일을 새 이름의 0.1 실행 파일로 교체한다.
- 실제 Android 기기의 공식 지원 시나리오와 안정화 검증이 모두 완료되기 전에는 버전을 1.0으로 올리지 않는다.
- Windows 수동 검증에서 정상 종료 뒤 관련 프로세스가 없고 프로그램 폴더 rename·삭제가 가능해야 안정화 완료로 판단한다.
- 제3자 바이너리와 Pokémon 상표·아이콘은 README와 `THIRD_PARTY_NOTICES.md`에서 출처와 확인 필요 사항을 분리한다.

## 완료 조건.

- [x] 목표와 비목표가 승인됐다.
- [x] 주요 흐름과 예외 흐름이 합의됐다.
- [x] 검증 방법과 완료 증거가 정의됐다.
- [x] 배포·복구 조건이 필요한 수준으로 정의됐다.
