# 🚀 Streamlit Cloud 배포 가이드

## 단계별 배포 방법

### 1. GitHub 리포지토리 생성
```bash
# GitHub에서 새 리포지토리 생성
# 리포지토리 이름: AutoAvatar
# Public으로 설정
```

### 2. 코드 업로드
```bash
git init
git add .
git commit -m "Initial AutoAvatar release"
git branch -M main
git remote add origin https://github.com/[your-username]/AutoAvatar.git
git push -u origin main
```

### 3. Streamlit Cloud 배포
1. https://share.streamlit.io/ 접속
2. "New app" 클릭
3. GitHub 리포지토리 연결
4. 설정:
   - Repository: your-username/AutoAvatar
   - Branch: main
   - Main file path: app.py

### 4. 환경변수 설정
Streamlit Cloud에서 "Advanced settings" → "Secrets":
```toml
[secrets]
OPENAI_API_KEY = "your_openai_key_here"
ELEVENLABS_API_KEY = "your_elevenlabs_key_here"
AZURE_SPEECH_KEY = "your_azure_key_here"
AZURE_SPEECH_REGION = "eastus"
```

### 5. 배포 완료
- 자동 배포 후 공개 URL 생성
- 예시: https://autoavatar-demo.streamlit.app/ 