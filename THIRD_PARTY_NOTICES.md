# Third-Party Notices and Release Checklist

이 문서는 저장소에 포함된 제3자 실행 파일의 출처 확인 결과와 배포 전 남은 라이선스 작업을 기록합니다. 법률 자문을 대신하지 않습니다.

## 확인한 배포본

2026-09-01에 저장소의 다음 파일을 공식 `scrcpy-win64-v4.0.zip`과 SHA-256으로 비교했습니다.

- `bin/adb/adb.exe`.
- `bin/adb/AdbWinApi.dll`.
- `bin/adb/AdbWinUsbApi.dll`.
- `bin/scrcpy/scrcpy.exe`.
- `bin/scrcpy/scrcpy-server`.
- `bin/scrcpy/SDL3.dll`.
- `bin/scrcpy/avcodec-62.dll`.
- `bin/scrcpy/avformat-62.dll`.
- `bin/scrcpy/avutil-60.dll`.
- `bin/scrcpy/swresample-6.dll`.
- `bin/scrcpy/libusb-1.0.dll`.

11개 파일 모두 공식 ZIP의 대응 파일과 일치했습니다. 공식 ZIP 자체의 SHA-256은 `75dbeb5b00e6f64292f26f70900ae55ca397786bdfb0b9bbeb481a0549047457`이었으며 scrcpy 4.0 Windows 문서에 게시된 값과 일치했습니다.

공식 출처는 다음과 같습니다.

- [scrcpy 4.0 release](https://github.com/Genymobile/scrcpy/releases/tag/v4.0).
- [scrcpy Windows release documentation](https://github.com/Genymobile/scrcpy/blob/v4.0/doc/windows.md).
- [scrcpy license](https://github.com/Genymobile/scrcpy/blob/v4.0/LICENSE).

## 구성요소별 확인 상태

### scrcpy

- 확인 버전은 4.0입니다.
- upstream `LICENSE`는 Apache License 2.0입니다.
- 원문은 [scrcpy v4.0 LICENSE](https://github.com/Genymobile/scrcpy/blob/v4.0/LICENSE)에서 확인했습니다.

### Android Debug Bridge와 Windows ADB DLL

- `adb version`에서 Android Debug Bridge 37.0.0으로 확인했습니다.
- 파일은 공식 scrcpy 4.0 Windows ZIP뿐 아니라 Google의 `platform-tools_r37.0.0-win.zip` 대응 파일과도 SHA-256이 일치합니다.
- Google 공식 ZIP의 SHA-256은 `4fe305812db074cea32903a489d061eb4454cbc90a49e8fea677f4b7af764918`입니다.
- 공식 배포본의 `NOTICE.txt` 원문을 `licenses/Android-Platform-Tools-37.0.0-NOTICE.txt`에 포함했습니다.

### SDL3

- `SDL3.dll`은 공식 scrcpy 4.0 Windows ZIP과 해시가 일치합니다.
- scrcpy 4.0 빌드 스크립트와 `scrcpy --version`에서 SDL 3.4.8을 확인했습니다.
- 해당 태그의 원문을 `licenses/SDL-3.4.8.txt`에 포함했습니다.

### FFmpeg libraries

- `avcodec-62.dll`, `avformat-62.dll`, `avutil-60.dll`, `swresample-6.dll`은 공식 scrcpy 4.0 Windows ZIP과 해시가 일치합니다.
- scrcpy 4.0의 공식 빌드 스크립트와 DLL 내부 버전·configure 문자열에서 FFmpeg 8.1.1을 확인했습니다.
- configure 문자열에는 `--enable-gpl`과 `--enable-nonfree`가 없고 각 DLL은 `LGPL version 2.1 or later`로 보고합니다.
- FFmpeg 라이선스 안내와 LGPL 2.1 원문을 `licenses/FFmpeg-8.1.1-LICENSE.md`, `licenses/FFmpeg-LGPL-2.1.txt`에 포함했습니다.
- 빌드에 정적으로 포함된 dav1d 1.5.3과 zlib 1.3.1의 라이선스·특허 고지도 `licenses/`에 포함했습니다.
- 공식 안내는 [FFmpeg License and Legal Considerations](https://ffmpeg.org/legal.html)입니다.
- 남은 작업은 공개 바이너리 Release에 정확한 FFmpeg 8.1.1 대응 소스와 scrcpy 4.0 빌드 스크립트를 같은 다운로드 위치에서 제공하는 것입니다.

### libusb

- `libusb-1.0.dll`은 공식 scrcpy 4.0 Windows ZIP과 해시가 일치합니다.
- scrcpy 4.0 빌드 스크립트와 `scrcpy --version`에서 libusb 1.0.29를 확인했습니다.
- 해당 태그의 원문을 `licenses/libusb-1.0.29.txt`에 포함했습니다.

## 기타 정리

- `bin/aapt.exe`는 Android Asset Packaging Tool v0.2-11948202였지만 런처에서 사용하지 않았습니다.
- `bin/aapt-arm-pie`는 실행 파일이 아니라 HTML 오류 페이지가 잘못 저장된 파일이었습니다.
- 두 파일 모두 런타임 호출과 기존 기능에 영향이 없어 0.1 배포 대상과 저장소에서 제거했습니다.
- APK에서 추출했던 기존 아이콘은 2026-09-01에 제거했습니다.
- 현재 `pokemon_icon.ico`와 `bin/scrcpy/pokemon_icon.ico`는 생성형 이미지로 제작한 독자적인 PC·스마트폰 연결 아이콘입니다.
- 승인된 PNG 원본은 `assets/launcher_icon.png`에 보존하며 Pokémon 캐릭터, 로고, 포켓볼과 게임 로고를 생성 조건에서 제외했습니다.

## 프로젝트 코드 라이선스

- 이 저장소는 `DOHA1012/pokemon-champions-pc`의 fork이며 원본 저장소에는 2026-09-01 기준 LICENSE가 없습니다.
- [GitHub의 공식 라이선스 안내](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)에 따라 LICENSE가 없는 코드는 기본 저작권법의 적용을 받습니다.
- 원저작자의 재배포 허가와 파생 프로젝트의 라이선스 조건을 확인하기 전에는 공개 바이너리 Release를 만들지 않습니다.

## 배포 차단 체크리스트

- [x] `licenses/` 디렉터리에 확인된 바이너리 버전의 라이선스 원문을 포함합니다.
- [x] ADB/Platform-Tools 37.0.0의 공식 NOTICE 원문과 바이너리 해시를 확인합니다.
- [x] FFmpeg 실제 빌드 옵션과 적용 라이선스를 확인합니다.
- [ ] FFmpeg 8.1.1 대응 소스와 scrcpy 4.0 빌드 스크립트를 Release 다운로드 위치에서 제공합니다.
- [x] 사용되지 않는 `aapt` 파일 두 개를 확인하고 제거합니다.
- [x] APK 추출 아이콘을 제거하고 독자적인 생성 이미지와 원본 PNG로 교체합니다.
- [ ] 원본 코드 저작자의 재배포 허가와 파생 프로젝트의 LICENSE 조건을 확인합니다.

위 항목이 끝나기 전에는 이 문서를 완전한 라이선스 고지로 간주하지 않습니다.
