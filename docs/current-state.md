# 프로젝트 현재 상태.

**갱신일:** 2026-09-01.

**기준 브랜치:** `main`.
**활성 작업:** Pokémon PC Launcher 0.2 scrcpy 4.1 native 리팩터링과 Release 준비.

## 제품·기술 기준선.

- 제품 목적: Android의 Pokémon 게임을 ADB와 scrcpy로 Windows 독립 창에 실행한다.
- 핵심 기술: Python 3.11, Tkinter, ADB 37.0.0, scrcpy 4.1, PyInstaller 6.20.0이다.
- 실행 환경: Windows PC와 USB 또는 Wi-Fi ADB가 활성화된 Android 기기다.
- 주요 제약: 자동 테스트로 검증할 수 없는 실제 게임·장치 동작은 연결된 Android 기기가 필요하다.

## 구현 상태.

- 완료: 0.1의 프로필·GUI·config migration·ADB ownership·graceful shutdown을 보존했다.
- 완료: Activity·display ID·force-stop·app-running 자체 구현을 삭제하고 scrcpy 4.1 `--start-app`·`--new-display`로 치환했다.
- 완료: `--keep-active`, 기본 OFF Flex Display, scrcpy 버전 검사와 통합 command builder를 구현했다.
- 완료: 공식 scrcpy 4.1 Windows x64 ZIP 구조와 dependency 라이선스 고지를 반영했다.
- 완료: PyInstaller 6.20.0으로 Tcl/Tk가 포함된 0.2 EXE를 재빌드했다.
- 완료: 최종 EXE의 WM_CLOSE 뒤 launcher·scrcpy·bundled ADB 잔존 0과 임시 배포 폴더 rename·delete를 확인했다.
- 완료: PyInstaller 실행 파일 빌드와 Windows GUI 시작·X 종료 smoke test다.
- 완료: 전체 diff와 코드 리뷰 지적 처리다.
- 완료: APK 추출 아이콘을 독자적인 PC·스마트폰 연결 아이콘으로 교체하고 PNG 원본을 보존했다.
- 대기: 두 실제 게임의 USB·Wi-Fi·Virtual Display·미러링 수동 검증이다.
- 실기기 확인: Samsung SM-S936N, Android 16, USB, Champions, Virtual Display 1280x720에서 display 생성·앱 실행·영상 출력은 정상이다.
- 알려진 문제: 위 환경에서 키보드·마우스 입력이 전달되지 않았다. 당시 `스마트폰 실제 화면 끄기`는 켜져 있었으나 인과관계는 아직 확인되지 않았다.
- 알려진 문제: 실제 게임 실행 뒤 Windows 폴더 잠금 해제는 Android 기기로 최종 검증해야 한다.
- 배포 게이트: 원본 저장소에 LICENSE가 없어 원저작자의 재배포 조건 확인 전에는 공개 Release를 만들지 않는다.
- 배포 준비: 정확한 scrcpy·ADB·SDL·FFmpeg·dav1d·zlib·libusb 라이선스 원문과 ADB NOTICE를 `licenses/`에 포함했다.
- 배포 준비: 사용되지 않은 `aapt.exe`와 HTML 오류 페이지였던 `aapt-arm-pie`를 제거했다.
- 남은 배포 게이트: 원저작자 허가와 FFmpeg 8.1.2 대응 소스·scrcpy 4.1 빌드 스크립트의 Release 동시 제공이다.

## 검증 기준선.

- 빌드: 루트 `Pokémon PC Launcher.exe`를 PyInstaller 6.20.0으로 생성했다.
- 테스트: `python -m unittest discover -v` 결과 66개 테스트, 성공이다.
- 정적 검사: 세 Python 모듈의 `py_compile`과 `git diff --check`가 성공했다.
- 수동 검증: Samsung SM-S936N, Android 16, USB에서 Champions Virtual Display 생성과 영상 출력은 성공했고 키보드·마우스 입력은 실패했다.
- 입력 진단: `launcher.log`에서 scrcpy 4.1이 display 13을 생성하고 Champions를 시작한 뒤 정상 종료한 것을 확인했다. 입력 차단 옵션이나 scrcpy 오류는 없었다.
- 입력 진단: 실패 당시 `turn_screen_off=true`였으며, 화면 끄기 해제 재시험과 기본 화면 미러링 입력 비교는 아직 대기 중이다.
- ADB 진단: 시작 전 server 없음, bundled `server-status` 호출 후 `bin/scrcpy/adb.exe` PID 생성, `kill-server` 후 PID 제거를 확인했다.
- 바이너리 진단: 공식 scrcpy 4.1 Windows x64 ZIP의 게시 SHA-256을 확인했고 `bin/scrcpy/`의 16개 파일이 공식 ZIP과 모두 일치했다.
- 코드 감소: `launcher_core.py`는 기준 831줄에서 657줄로 174줄 감소했다.
- 라이선스 진단: 9개 원문 파일이 정확한 upstream 태그 또는 Google Platform-Tools 37.0.0 배포본과 SHA-256이 일치했다.
- Windows smoke: 최종 GUI 제목과 X 종료를 확인했고 launcher·bundled adb·bundled scrcpy 잔류가 모두 0이었다. 임시 배포 폴더의 rename과 삭제도 성공했다.
- 0.2 Windows smoke: GUI 제목 `Pokémon PC Launcher 0.2 - Pokémon Champions`, scrcpy 4.1 버전 로그, launcher-owned ADB server 종료를 확인했고 임시 배포 폴더의 rename·delete가 즉시 성공했다.
- Release 준비 smoke: `aapt` 제거 후 임시 배포 폴더에서 EXE 창에 WM_CLOSE를 보내 정상 종료했고 해당 경로의 잔류 프로세스 0개, 폴더 rename과 삭제 성공을 다시 확인했다.
- 아이콘: 1254x1254 RGBA 원본과 16·24·32·48·64·128·256픽셀 ICO 프레임을 확인했고 EXE 내 32픽셀 아이콘을 추출해 새 디자인을 확인했다.
- 아이콘 빌드 smoke: 실제 Windows 사용자 컨텍스트에서 PyInstaller가 Tcl/Tk를 포함해 빌드됐으며 GUI 자식 창 두 개를 정상 종료한 뒤 작업 사본의 launcher·ADB·scrcpy 잔류가 0개였다.
- 시각 자동화: Computer Use native helper pipe가 없어 스크린샷 기반 위젯 검증은 수행하지 못했다.

## 다음 작업.

1. 원본 저장소 저작자에게 코드 재배포 라이선스를 확인한다.
2. 공개 Release에 FFmpeg 8.1.2 대응 소스와 scrcpy 4.1 빌드 스크립트를 함께 제공한다.
3. SM-S936N에서 화면 끄기 해제 후 Champions Virtual Display 입력과 기본 화면 미러링 입력을 비교한다.
4. 실제 Android 기기에서 두 게임의 나머지 USB·Wi-Fi·Virtual·Mirror·Flex와 종료 뒤 폴더 rename·삭제를 검증한다.
