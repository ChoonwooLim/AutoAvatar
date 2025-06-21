# 🖥️ AutoAvatar Desktop Application

AutoAvatar를 독립적인 데스크톱 애플리케이션으로 실행할 수 있습니다!

## 🚀 빠른 시작

### 1️⃣ 사전 요구사항

**필수 설치:**
- **Node.js** (v16 이상): https://nodejs.org
- **Python** (3.8 이상): 이미 설치됨
- **Git**: 이미 설치됨

**설치 확인:**
```bash
node --version
npm --version
python --version
```

### 2️⃣ 개발 모드 실행

```bash
# 간단한 실행
python run-desktop.py

# 또는 수동 실행
npm install
npm run dev
```

### 3️⃣ EXE 파일 빌드

```bash
# 자동 빌드
python build-desktop.py

# 또는 수동 빌드
npm install
npm run build-win
```

## 📁 프로젝트 구조

```
AutoAvatar/
├── electron/                 # Electron 관련 파일
│   ├── main.js              # 메인 프로세스
│   ├── preload.js           # Preload 스크립트
│   └── assets/              # 아이콘 및 자산
├── package.json             # npm 설정
├── build-desktop.py         # 빌드 스크립트
├── run-desktop.py          # 개발 실행 스크립트
└── dist/                   # 빌드 결과 (생성됨)
```

## 🛠️ 개발 가이드

### 개발 모드 실행
```bash
python run-desktop.py
```

**특징:**
- 🔄 자동 리로딩
- 🔍 개발자 도구 활성화
- 📝 콘솔 로그 출력

### 프로덕션 빌드
```bash
python build-desktop.py
```

**생성되는 파일:**
- `dist/AutoAvatar Setup.exe` - Windows 설치 프로그램
- `dist/win-unpacked/` - 압축 해제된 앱 폴더

## 🎯 주요 기능

### ✅ 독립 실행
- Python 환경 불필요
- 모든 의존성 포함
- 더블클릭으로 실행

### ✅ 네이티브 느낌
- 시스템 메뉴 통합
- 파일 연결 지원
- 바탕화면 바로가기

### ✅ 보안 강화
- 컨텍스트 메뉴 비활성화
- 개발자 도구 제한
- 안전한 IPC 통신

## 🔧 고급 설정

### 아이콘 변경
1. `electron/assets/` 폴더에 아이콘 파일 추가:
   - `icon.ico` (Windows)
   - `icon.png` (Linux)
   - `icon.icns` (macOS)

### 빌드 옵션 수정
`package.json`의 `build` 섹션에서 설정 변경:

```json
{
  "build": {
    "appId": "com.autoavatar.desktop",
    "productName": "AutoAvatar",
    "win": {
      "target": "nsis",
      "icon": "electron/assets/icon.ico"
    }
  }
}
```

## 🐛 문제 해결

### Node.js 설치 문제
```bash
# Node.js 다운로드
https://nodejs.org/en/download/

# 설치 확인
node --version
npm --version
```

### 빌드 실패
```bash
# 캐시 정리
npm cache clean --force
rm -rf node_modules
npm install

# 다시 빌드
python build-desktop.py
```

### Streamlit 연결 실패
```bash
# Python 패키지 재설치
pip install -r requirements.txt

# 포트 충돌 확인
netstat -an | findstr :8501
```

## 📦 배포

### Windows 배포
1. `dist/AutoAvatar Setup.exe` 파일 배포
2. 사용자가 설치 프로그램 실행
3. 바탕화면 바로가기 자동 생성

### 포터블 버전
1. `dist/win-unpacked/` 폴더 압축
2. 압축 파일 배포
3. 압축 해제 후 `AutoAvatar.exe` 실행

## 🚀 성능 최적화

### 앱 크기 줄이기
- 불필요한 Python 패키지 제거
- 이미지 파일 최적화
- 캐시 파일 정리

### 실행 속도 향상
- Streamlit 캐시 활용
- 지연 로딩 구현
- 메모리 사용량 최적화

## 📞 지원

문제가 발생하면:
1. 터미널에서 오류 메시지 확인
2. `npm run dev`로 개발 모드 테스트
3. 로그 파일 확인

---

🎉 **이제 AutoAvatar를 독립적인 데스크톱 앱으로 사용할 수 있습니다!** 