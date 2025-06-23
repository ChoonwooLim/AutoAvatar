import streamlit as st
import openai
import os
from PIL import Image

# 페이지 설정
st.set_page_config(
    page_title="AutoAvatar - AI 뉴스 스크립트 생성기",
    page_icon="🎬",
    layout="wide"
)

# CSS 스타일
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

def get_openai_key():
    """OpenAI API 키 가져오기"""
    # 환경변수에서 먼저 시도 (로컬용)
    if "OPENAI_API_KEY" in os.environ:
        return os.environ["OPENAI_API_KEY"]
    
    # Streamlit Secrets에서 시도 (Cloud용) - 안전하게 처리
    try:
        if hasattr(st, 'secrets') and "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass  # secrets가 없어도 무시
    
    return None

def generate_news_script(topic, duration, style):
    """뉴스 스크립트 생성"""
    api_key = get_openai_key()
    
    # 세션 상태에서도 확인
    if not api_key and 'temp_api_key' in st.session_state:
        api_key = st.session_state.temp_api_key
    
    if not api_key:
        st.error("❌ OpenAI API 키가 설정되지 않았습니다!")
        st.info("위의 'API 키 입력' 섹션에서 키를 입력해주세요.")
        return None
    
    # OpenAI 클라이언트 초기화
    client = openai.OpenAI(api_key=api_key)
    
    # 프롬프트 생성
    prompt = f"""
    다음 뉴스 주제로 {duration}초 분량의 전문적인 뉴스 스크립트를 한국어로 작성해주세요.
    
    주제: {topic}
    스타일: {style}
    길이: 약 {duration}초 (약 {duration * 3}단어)
    
    요구사항:
    1. 뉴스 앵커가 읽을 수 있는 자연스러운 톤
    2. 정확하고 객관적인 정보 전달
    3. 적절한 구두점과 쉼표 사용
    4. "안녕하세요" 인사말로 시작
    5. "지금까지 뉴스였습니다" 마무리
    
    스크립트만 출력하고 다른 설명은 포함하지 마세요.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 전문 뉴스 스크립트 작가입니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        st.error(f"❌ 스크립트 생성 오류: {str(e)}")
        return None

def main():
    # 헤더
    st.markdown("""
    <div class="main-header">
        <h1>🎬 AutoAvatar</h1>
        <h3>AI 뉴스 스크립트 생성기 (Cloud Edition)</h3>
        <p>뉴스 주제를 입력하면 전문적인 스크립트를 자동 생성합니다</p>
    </div>
    """, unsafe_allow_html=True)
    
    # API 키 상태 확인 및 입력
    api_key = get_openai_key()
    
    if not api_key:
        st.warning("⚠️ OpenAI API 키를 설정해주세요")
        
        # 로컬에서 API 키 직접 입력
        with st.expander("🔑 API 키 입력", expanded=True):
            input_key = st.text_input(
                "OpenAI API 키를 입력하세요:",
                type="password",
                placeholder="sk-..."
            )
            
            if input_key:
                # 세션 상태에 저장
                st.session_state.temp_api_key = input_key
                st.success("✅ API 키가 입력되었습니다!")
                st.rerun()
            
            st.info("""
            **API 키 획득 방법:**
            1. [OpenAI 웹사이트](https://platform.openai.com/api-keys) 접속
            2. 로그인 후 API Keys 메뉴
            3. "Create new secret key" 클릭
            4. 생성된 키를 복사해서 위에 입력
            
            **Streamlit Cloud 배포시:**
            - 앱 설정 → Secrets 탭에서 설정
            """)
    else:
        st.success("✅ OpenAI API 키가 설정되었습니다")
    
    # 세션 상태에서 임시 API 키 확인
    if not api_key and 'temp_api_key' in st.session_state:
        api_key = st.session_state.temp_api_key
    
    # 메인 인터페이스
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📸 이미지 업로드")
        uploaded_file = st.file_uploader(
            "이미지 파일을 선택하세요",
            type=['png', 'jpg', 'jpeg'],
            help="뉴스에 사용할 이미지를 업로드하세요"
        )
        
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="업로드된 이미지", use_container_width=True)
    
    with col2:
        st.header("📝 뉴스 주제")
        
        # 예시 주제들
        with st.expander("💡 예시 주제들"):
            examples = [
                "손흥민 레알 마드리드 이적설",
                "AI 기술 의료 분야 혁신",
                "기후변화 대응 국제 협력",
                "새로운 스마트폰 기술 발표"
            ]
            for i, example in enumerate(examples):
                if st.button(f"📰 {example}", key=f"ex_{i}"):
                    st.session_state.topic = example
        
        # 주제 입력
        topic = st.text_area(
            "뉴스 주제를 입력하세요:",
            value=st.session_state.get('topic', ''),
            height=100,
            placeholder="예: 손흥민 레알 마드리드 이적 확정"
        )
        
        # 설정
        col_a, col_b = st.columns(2)
        with col_a:
            duration = st.slider("길이 (초)", 15, 60, 30)
        with col_b:
            style = st.selectbox("스타일", ["Modern", "Classic", "Dramatic"])
        
        # 생성 버튼
        if st.button("🚀 스크립트 생성", type="primary", use_container_width=True):
            if not topic.strip():
                st.error("뉴스 주제를 입력해주세요!")
            elif not api_key:
                st.error("OpenAI API 키를 설정해주세요!")
            else:
                with st.spinner("스크립트 생성 중..."):
                    script = generate_news_script(topic, duration, style)
                    
                    if script:
                        st.success("🎉 스크립트 생성 완료!")
                        
                        # 스크립트 표시
                        st.markdown("### 📝 생성된 스크립트")
                        st.text_area("", value=script, height=300, disabled=True)
                        
                        # 통계
                        word_count = len(script.split())
                        col_x, col_y, col_z = st.columns(3)
                        with col_x:
                            st.metric("단어 수", word_count)
                        with col_y:
                            st.metric("예상 길이", f"{duration}초")
                        with col_z:
                            st.metric("말하기 속도", f"{word_count*60//duration} WPM")
                        
                        # 다운로드
                        st.download_button(
                            "📥 스크립트 다운로드",
                            script,
                            f"script_{topic[:10]}.txt",
                            "text/plain"
                        )

if __name__ == "__main__":
    main()
    
    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>🎬 AutoAvatar - AI 뉴스 스크립트 생성기</p>
        <p>❤️ Made with Streamlit & OpenAI</p>
    </div>
    """, unsafe_allow_html=True) 