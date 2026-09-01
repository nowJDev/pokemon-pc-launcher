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
- 파일은 공식 scrcpy 4.0 Windows ZIP의 대응 파일과 해시가 일치합니다.
- TODO: 배포 전에 해당 Platform-Tools 배포본에 적용되는 Google/AOSP 라이선스와 NOTICE 원문을 공식 배포 패키지에서 추출해 `licenses/`에 포함해야 합니다.

### SDL3

- `SDL3.dll`은 공식 scrcpy 4.0 Windows ZIP과 해시가 일치합니다.
- SDL upstream 원문은 [SDL LICENSE.txt](https://github.com/libsdl-org/SDL/blob/main/LICENSE.txt)에서 확인할 수 있습니다.
- TODO: 정확한 SDL 빌드 버전의 LICENSE 원문을 배포물의 `licenses/SDL.txt`에 포함해야 합니다.

### FFmpeg libraries

- `avcodec-62.dll`, `avformat-62.dll`, `avutil-60.dll`, `swresample-6.dll`은 공식 scrcpy 4.0 Windows ZIP과 해시가 일치합니다.
- FFmpeg는 빌드 구성에 따라 적용 조건이 달라질 수 있다고 공식 법률 안내에서 설명합니다.
- 공식 안내는 [FFmpeg License and Legal Considerations](https://ffmpeg.org/legal.html)입니다.
- TODO: scrcpy 4.0 Windows release의 실제 FFmpeg configure 옵션과 소스 제공 의무를 확인하고, 정확한 LGPL/GPL 원문과 필요한 소스 링크 또는 제공물을 배포본에 추가해야 합니다.

### libusb

- `libusb-1.0.dll`은 공식 scrcpy 4.0 Windows ZIP과 해시가 일치합니다.
- upstream 원문은 [libusb COPYING](https://github.com/libusb/libusb/blob/master/COPYING)에서 확인할 수 있습니다.
- TODO: 공식 scrcpy 4.0 빌드에 사용된 정확한 libusb 버전의 COPYING 원문을 배포물의 `licenses/libusb.txt`에 포함해야 합니다.

## 아직 확인하지 않은 파일

- `bin/aapt.exe`와 `bin/aapt-arm-pie`는 scrcpy 4.0 ZIP에 없으며 현재 Python 런처에서 사용하지 않습니다.
- TODO: 두 파일의 출처, 버전, 실제 필요 여부와 적용 라이선스를 확인하기 전에는 새 배포본에 포함하지 않습니다. 확인 없이 삭제하지도 않습니다.
- `pokemon_icon.ico`와 동일 아이콘 복사본의 권리 관계는 저장소에서 확인할 수 없습니다.
- TODO: 재배포 권한이 확인된 자체 아이콘으로 교체하거나 권리 근거를 문서화해야 합니다.

## 배포 차단 체크리스트

- [ ] `licenses/` 디렉터리에 각 정확한 바이너리 버전의 라이선스 원문을 포함합니다.
- [ ] ADB/Platform-Tools NOTICE와 배포 조건을 확인합니다.
- [ ] FFmpeg 실제 빌드 옵션과 대응 소스 제공 의무를 확인합니다.
- [ ] `aapt` 파일의 출처와 필요성을 확인합니다.
- [ ] 아이콘 재배포 권리를 확인합니다.
- [ ] 프로젝트 자체 코드의 LICENSE를 저장소 소유자가 선택합니다.

위 항목이 끝나기 전에는 이 문서를 완전한 라이선스 고지로 간주하지 않습니다.
