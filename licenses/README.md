# 제3자 라이선스 원문.

이 디렉터리는 저장소에 포함된 실행 파일의 정확한 버전을 기준으로 원문 라이선스와 고지를 보관합니다. 이 파일들은 Pokémon PC Launcher 자체 코드의 라이선스를 정하지 않습니다.

| 구성요소 | 확인 버전 | 포함 원문 | 공식 소스 |
| --- | --- | --- | --- |
| scrcpy | 4.0 | `scrcpy-4.0.txt` | <https://github.com/Genymobile/scrcpy/tree/v4.0> |
| Android SDK Platform-Tools | 37.0.0 | `Android-Platform-Tools-37.0.0-NOTICE.txt` | <https://developer.android.com/tools/releases/platform-tools> |
| SDL | 3.4.8 | `SDL-3.4.8.txt` | <https://github.com/libsdl-org/SDL/tree/release-3.4.8> |
| FFmpeg | 8.1.1 | `FFmpeg-8.1.1-LICENSE.md`, `FFmpeg-LGPL-2.1.txt` | <https://ffmpeg.org/releases/ffmpeg-8.1.1.tar.xz> |
| dav1d | 1.5.3 | `dav1d-1.5.3.txt`, `dav1d-1.5.3-PATENTS.txt` | <https://github.com/videolan/dav1d/tree/1.5.3> |
| zlib | 1.3.1 | `zlib-1.3.1.txt` | <https://github.com/madler/zlib/tree/v1.3.1> |
| libusb | 1.0.29 | `libusb-1.0.29.txt` | <https://github.com/libusb/libusb/tree/v1.0.29> |

scrcpy 4.0의 Windows 빌드 스크립트는 FFmpeg를 공유 라이브러리로 만들고 dav1d를 정적으로 연결합니다. 저장소의 FFmpeg DLL에 기록된 configure 문자열과 버전 문자열로 FFmpeg 8.1.1, LGPL 2.1+, zlib 1.3.1을 다시 확인했습니다.

공개 바이너리 Release 전에는 FFmpeg 8.1.1의 정확한 대응 소스와 scrcpy 4.0 빌드 스크립트를 같은 다운로드 위치에서 제공할 방법을 확정해야 합니다. 자세한 배포 상태는 루트의 `THIRD_PARTY_NOTICES.md`를 따릅니다.
