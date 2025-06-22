# 🚀 AutoAvatar Streamlit Cloud 배포 가이드

## 📋 배포 준비사항

### 1. 필요한 파일들
- `app_cloud.py` - Cloud용 간소화된 앱
- `requirements_cloud.txt` - Cloud용 패키지 목록
- `packages.txt` - 시스템 패키지
- `.streamlit/config.toml` - Streamlit 설정

### 2. GitHub 저장소 준비
```bash
git add app_cloud.py requirements_cloud.txt packages.txt .streamlit/
git commit -m "Add Streamlit Cloud deployment files"
git push origin main
```

## 🌐 Streamlit Cloud 배포 단계

### 1단계: Streamlit Cloud 접속
1. [share.streamlit.io](https://share.streamlit.io) 접속
2. GitHub 계정으로 로그인

### 2단계: 새 앱 배포
1. **"New app"** 버튼 클릭
2. GitHub 저장소 선택
3. 브랜치: `main`
4. 메인 파일: `app_cloud.py`
5. **"Deploy!"** 클릭

### 3단계: 환경 변수 설정
**Advanced settings** → **Secrets**에서 설정:

```toml
# .streamlit/secrets.toml 형식
OPENAI_API_KEY = "your-openai-api-key-here"
```

## 🔧 문제 해결

### 자주 발생하는 오류들

#### 1. Requirements 설치 오류
```
Error installing requirements
```

**해결방법:**
- `requirements_cloud.txt` 사용
- 문제가 되는 패키지 제거 (PyAudio, MoviePy 등)

#### 2. 모듈 import 오류
```
ModuleNotFoundError: No module named 'pyaudio'
```

**해결방법:**
- 코드에서 선택적 import 사용
- try-except 블록으로 처리

#### 3. 시스템 패키지 오류
```
ffmpeg not found
```

**해결방법:**
- `packages.txt` 파일에 시스템 패키지 추가
- Cloud 환경에서 지원되지 않는 기능은 비활성화

## 📦 Cloud vs Local 기능 비교

| 기능 | Local | Cloud |
|------|-------|-------|
| 스크립트 생성 | ✅ | ✅ |
| 이미지 업로드 | ✅ | ✅ |
| API 키 관리 | ✅ | ✅ |
| 음성 녹음 | ✅ | ❌ |
| 비디오 생성 | ✅ | ❌ |
| 고급 TTS | ✅ | ❌ |
| 음성 복제 | ✅ | ❌ |

## 💡 최적화 팁

### 1. 빠른 로딩
- 불필요한 패키지 제거
- 지연 로딩 사용
- 캐싱 활용

### 2. 메모리 효율성
```python
@st.cache_data
def load_model():
    # 모델 로딩 코드
    pass
```

### 3. 사용자 경험
- 로딩 상태 표시
- 오류 메시지 개선
- 기능 제한 안내

## 🔗 유용한 링크

- [Streamlit Cloud 문서](https://docs.streamlit.io/streamlit-cloud)
- [배포 문제 해결](https://docs.streamlit.io/streamlit-cloud/troubleshooting)
- [GitHub 연동](https://docs.streamlit.io/streamlit-cloud/get-started/connect-your-github-account)

## 📞 지원

배포 중 문제가 발생하면:
1. 로그 확인 (Streamlit Cloud 대시보드)
2. GitHub Issues 생성
3. Streamlit Community 포럼 활용 