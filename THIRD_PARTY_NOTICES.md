# Third-Party Notices and Release Checklist.

이 문서는 저장소에 포함된 제3자 실행 파일의 출처 확인 결과와 배포 전 남은 라이선스 작업을 기록합니다. 법률 자문을 대신하지 않습니다.

## 확인한 배포본.

2026-09-01에 `bin/scrcpy/`를 공식 `scrcpy-win64-v4.1.zip`의 내용으로 교체했습니다. 공식 ZIP의 SHA-256은 `5b12172b3264b2889f4583ee64752ce832e29bc8b1089dca81093459697165db`이며 scrcpy 4.1 Windows 문서의 게시값과 일치합니다.

공식 ZIP의 16개 파일을 저장소의 대응 파일과 각각 SHA-256으로 비교했으며 모두 일치했습니다. 별도였던 `bin/adb/`는 제거하고 공식 ZIP처럼 ADB와 DLL을 `bin/scrcpy/`에 함께 보관합니다.

| 파일 | SHA-256 |
| --- | --- |
| `scrcpy.exe` | `575ca1284345c7b3975585bc61b66d564a9a4f1ecb28fbb4c599c92a124054a9` |
| `scrcpy-server` | `deacb991ed2509715160ffdc7907e47b4160eb30d1566217e9047fd5b8850cae` |
| `adb.exe` | `957e46b8615f7af5b7292a2ddabe98d2e61940c3fb2b0545756507f080613e71` |
| `AdbWinApi.dll` | `120bef587119c6cb926b86b9be90fdfbce38937588eae28cd91a94ce63c7b965` |
| `AdbWinUsbApi.dll` | `6ca69a2ca0e31309c087d288f058977d421ad03500e4c3e1dbd981241a069c60` |
| `SDL3.dll` | `0619eb2da6032984dc6e2098897aeacdbd66b0415bb87bc03e628159ba60b15d` |
| `avcodec-62.dll` | `7179de2b132e78eb0a76458a0a3859dfe1edcbb6d2eeb4a456f03f7ae96d5b66` |
| `avformat-62.dll` | `7232316acce00371d89f589748b570d95885ea6bbfc1972a0a9d3b884903eee1` |
| `avutil-60.dll` | `3d6170dd68549c6f39b8d8710a37f79d9678905df705a8b0a6bc7ea9037daddf` |
| `swresample-6.dll` | `4cc809d2cd822e186906fbc9d8a0acffa937e35de1282b2e2ab7346cfed96fed` |
| `libusb-1.0.dll` | `8ec130918a476b0dbd114c803e71314360608ceabdd2b6f38c83f6f208c608e0` |

공식 출처는 다음과 같습니다.

- [scrcpy 4.1 release](https://github.com/Genymobile/scrcpy/releases/tag/v4.1).
- [scrcpy 4.1 Windows release documentation](https://github.com/Genymobile/scrcpy/blob/v4.1/doc/windows.md).
- [scrcpy 4.1 dependency build scripts](https://github.com/Genymobile/scrcpy/tree/v4.1/app/deps).
- [scrcpy 4.1 license](https://github.com/Genymobile/scrcpy/blob/v4.1/LICENSE).

## 구성요소별 확인 상태.

### scrcpy.

- `scrcpy --version`에서 4.1을 확인했습니다.
- 공식 ZIP의 `LICENSE.txt`와 `licenses/scrcpy-4.1.txt`는 같은 Apache License 2.0 원문입니다.

### Android Debug Bridge와 Windows ADB DLL.

- `adb version`에서 Android Debug Bridge 37.0.0, build `37.0.0-14910828`을 확인했습니다.
- ADB 3개 파일은 공식 scrcpy 4.1 Windows ZIP과 일치합니다.
- 이전 검증에서 Google `platform-tools_r37.0.0-win.zip`의 대응 파일과도 일치했으며 공식 ZIP SHA-256은 `4fe305812db074cea32903a489d061eb4454cbc90a49e8fea677f4b7af764918`입니다.
- 공식 배포본의 `NOTICE.txt` 원문을 `licenses/Android-Platform-Tools-37.0.0-NOTICE.txt`에 포함했습니다.

### SDL3.

- `scrcpy --version`과 v4.1 `app/deps/sdl.sh`에서 SDL 3.4.12를 확인했습니다.
- `licenses/SDL-3.4.12.txt`는 `release-3.4.12` 태그의 원문과 일치합니다.

### FFmpeg libraries.

- `scrcpy --version`, DLL 버전 문자열과 v4.1 `app/deps/ffmpeg.sh`에서 FFmpeg 8.1.2를 확인했습니다.
- configure 문자열에는 `--enable-gpl`과 `--enable-nonfree`가 없고 각 DLL은 `LGPL version 2.1 or later`로 보고합니다.
- build script와 DLL 문자열에서 정적 의존성 dav1d 1.5.3과 zlib 1.3.1을 확인했습니다.
- `licenses/FFmpeg-8.1.2-LICENSE.md`, `licenses/FFmpeg-LGPL-2.1.txt`, dav1d·zlib 원문을 포함했습니다.
- 남은 작업은 공개 바이너리 Release에 정확한 FFmpeg 8.1.2 대응 소스와 scrcpy 4.1 build script를 같은 다운로드 위치에서 제공하는 것입니다.

### libusb.

- `scrcpy --version`과 v4.1 `app/deps/libusb.sh`에서 libusb 1.0.30을 확인했습니다.
- `licenses/libusb-1.0.30.txt`는 v1.0.30 태그의 원문과 일치합니다.

## 기타 정리.

- 사용하지 않던 `aapt.exe`와 HTML 오류 파일 `aapt-arm-pie`는 0.1에서 제거한 상태를 유지합니다.
- APK에서 추출했던 기존 아이콘은 사용하지 않습니다.
- 현재 `pokemon_icon.ico`와 `assets/launcher_icon.png`는 생성형 이미지로 제작한 독자적인 PC·스마트폰 연결 아이콘입니다.
- `bin/scrcpy/`에는 공식 ZIP 파일만 두어 upstream 배포 구조를 보존합니다.

## 프로젝트 코드 라이선스.

- 이 저장소는 `DOHA1012/pokemon-champions-pc`의 fork이며 원본 저장소에는 2026-09-01 기준 LICENSE가 없습니다.
- [GitHub의 공식 라이선스 안내](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)에 따라 LICENSE가 없는 코드는 기본 저작권법의 적용을 받습니다.
- 원저작자의 재배포 허가와 파생 프로젝트의 라이선스 조건을 확인하기 전에는 공개 바이너리 Release를 만들지 않습니다.

## 배포 차단 체크리스트.

- [x] scrcpy 4.1 공식 Windows x64 ZIP과 bundled 16개 파일을 검증합니다.
- [x] 실제 dependency 버전의 라이선스 원문과 ADB NOTICE를 `licenses/`에 포함합니다.
- [x] FFmpeg 실제 build 옵션과 적용 라이선스를 확인합니다.
- [ ] FFmpeg 8.1.2 대응 소스와 scrcpy 4.1 build script를 Release 다운로드 위치에서 제공합니다.
- [x] 사용되지 않는 `aapt` 파일과 APK 추출 아이콘을 제거합니다.
- [ ] 원본 코드 저작자의 재배포 허가와 파생 프로젝트의 LICENSE 조건을 확인합니다.

위 항목이 끝나기 전에는 이 문서를 완전한 라이선스 고지로 간주하지 않습니다.
