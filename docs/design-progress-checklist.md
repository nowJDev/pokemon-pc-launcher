# 설계·구현 진행 체크리스트.

## 현재 단계.

- 단계: 0.2 scrcpy 4.1 native 리팩터링과 Windows 검증 완료, 실제 Android 기기·공개 Release 게이트 대기.
- 기준 브랜치: `main`.

## 요구사항 추적.

| ID | 요구사항 | 상태 | 구현 위치 | 검증 증거 | 위험·메모 |
|---|---|---|---|---|---|
| R-001 | 두 게임 프로필과 게임 선택 GUI | 구현 완료 | `game_profiles.py`, `pokemon_launcher.py` | 프로필·GUI 계약 테스트 통과 | 실제 두 게임 실행은 기기 검증이 필요하다. |
| R-002 | ADB 상태, Wi-Fi 검증, IP 탐색과 연결 해제 | 구현 완료 | `launcher_core.py` | 파서·서비스 단위 테스트 통과 | 제조사별 명령 출력은 실제 기기 검증이 필요하다. |
| R-003 | 패키지 설치와 native 앱 실행 | 구현 완료 | `launcher_core.py`, `pokemon_launcher.py` | package·command builder 테스트 통과 | Activity 탐색 없이 `--start-app=+PACKAGE`를 사용한다. |
| R-004 | Virtual Display와 미러링 모드 | 일부 완료 | `launcher_core.py`, `pokemon_launcher.py` | 네 게임·모드 조합 인자 테스트 통과, SM-S936N 영상 출력 확인 | Android 16 Champions Virtual Display에서 키보드·마우스 입력 실패를 확인했다. 화면 끄기 해제와 기본 미러링 비교가 필요하다. |
| R-005 | 해상도·Flex·FPS·화면 옵션과 config 호환성 | 구현 완료 | 프로필·core·GUI | 해상도·0.1 config·Flex 테스트 통과 | Flex는 기본 OFF다. |
| R-006 | 로그, timeout, 바이너리 경로와 정상 종료 | 구현 완료 | core·GUI | ADB 소유권·scrcpy·worker 테스트 통과 | 실제 게임 종료 뒤 폴더 rename·삭제 검증은 남았다. |
| R-007 | README, 보안, 제3자 고지 | 일부 완료 | `README.md`, `THIRD_PARTY_NOTICES.md`, `licenses/` | scrcpy 4.1 공식 ZIP 16개 파일과 원문 고지 확인 | 원저작자 허가와 FFmpeg 대응 소스 Release 제공이 남았다. |
| R-008 | 단위 테스트와 0.2 실행 파일 | 구현 완료 | `tests/`, 루트 exe | 66개 unittest·PyInstaller·GUI 종료·폴더 잠금 smoke 통과 | 1.0 승격 전 실제 Android 안정화 검증이 필요하다. |

## 단계별 게이트.

- [x] 현재 기준선과 변경 범위를 확인했다.
- [x] 설계 명세가 승인됐다.
- [x] 구현 계획이 승인됐다.
- [x] 각 작업의 테스트·검증 증거를 기록했다.
- [x] Android 기기 제외 자동·Windows smoke 검증이 통과했다.
- [x] 코드 리뷰 지적을 처리했다.
- [x] 현재 상태 문서를 갱신했다.
- [ ] 검증된 변경을 한글 커밋으로 기록한다.
