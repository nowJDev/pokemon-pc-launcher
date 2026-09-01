# Pokémon PC Launcher 독자 아이콘 적용 계획.

> **For agentic workers: REQUIRED SUB-SKILL:** `executing-plans`를 사용하며 모든 단계는 아래 체크박스와 증거를 따른다.

**목표:** APK에서 추출한 기존 아이콘을 사용자가 승인한 독자적인 연결 화면 아이콘으로 교체하고 Windows 실행 파일에 반영한다.

**아키텍처:** 생성된 PNG를 추적 가능한 원본으로 보존하고, 기존 코드 호환성을 위해 루트와 scrcpy 폴더의 `pokemon_icon.ico` 파일명은 유지한다.

**기술 스택:** PNG, Windows ICO, Pillow, PyInstaller 6.20.0, Python `unittest`.

### Task 1. 원본 이미지와 ICO 자산.

**영향 파일.**

- 생성: `assets/launcher_icon.png`.
- 교체: `pokemon_icon.ico`.
- 교체: `bin/scrcpy/pokemon_icon.ico`.

**구현·검증 체크리스트.**

- [x] 승인 이미지 `exec-68261314-563a-444c-82aa-680a8ebbece2.png`를 `assets/launcher_icon.png`로 복사한다.
- [x] Pillow로 16, 24, 32, 48, 64, 128, 256 픽셀 프레임을 포함한 `pokemon_icon.ico`를 생성한다.

```powershell
python -c "from PIL import Image; image=Image.open('assets/launcher_icon.png').convert('RGBA'); image.save('pokemon_icon.ico', sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])"
```

- [x] 생성된 ICO를 `bin/scrcpy/pokemon_icon.ico`에 복사한다.
- [x] PNG가 RGBA이고 ICO에 7개 크기가 포함되며 두 ICO의 SHA-256이 같은지 확인한다.

### Task 2. 배포 문서와 실행 파일.

**영향 파일.**

- 수정: `THIRD_PARTY_NOTICES.md`.
- 수정: `docs/superpowers/specs/2026-09-01-multigame-launcher-design.md`.
- 수정: `docs/current-state.md`.
- 교체: `Pokémon PC Launcher.exe`.

**구현·검증 체크리스트.**

- [x] APK 추출 아이콘이 제거되고 생성형 이미지 기반 독자 자산으로 교체됐음을 문서화한다.
- [x] PyInstaller로 아이콘이 포함된 Windows 실행 파일을 재빌드한다.

```powershell
pyinstaller --noconfirm --clean --onefile --windowed --name "Pokémon PC Launcher" --icon pokemon_icon.ico pokemon_launcher.py
```

- [x] `dist/Pokémon PC Launcher.exe`를 루트 실행 파일로 교체한다.
- [x] 실행 파일이 시작되고 X 종료 후 launcher, bundled adb, bundled scrcpy 프로세스가 남지 않는지 확인한다.

### Task 3. 검증과 통합.

**영향 파일.**

- 테스트: 전체 저장소.

**구현·검증 체크리스트.**

- [x] `python -m unittest discover -v`에서 68개 테스트 통과를 확인한다.
- [x] Python 모듈 compileall과 `git diff --check`를 통과시킨다.
- [x] EXE에 포함된 32픽셀 아이콘을 렌더링해 형태와 투명도를 확인한다.
- [x] 전체 diff에서 기존 코드와 사용자 파일이 의도치 않게 변경되지 않았는지 검토한다.
- [ ] 한글 커밋 후 `main`에 fast-forward 병합하고 원격에 push한다.
- [x] 원본 저장소의 LICENSE 부재가 해결되기 전에는 공개 Release 대신 배포 게이트 상태를 보고한다.
