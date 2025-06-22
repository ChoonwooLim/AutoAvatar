import streamlit as st
import os
import tempfile
import time
from PIL import Image
from config import Config
from utils.script_generator import ScriptGenerator
from utils.api_key_ui import render_api_key_setup

# 페이지 설정
st.set_page_config(
    page_title="AutoAvatar - AI 뉴스 비디오 생성기",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
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

.feature-box {
    background: #f8f9fa;
    padding: 1.5rem;
    border-radius: 10px;
    border-left: 5px solid #667eea;
    margin: 1rem 0;
}

.info-box {
    background: #e3f2fd;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #2196f3;
    margin: 1rem 0;
}

.error-box {
    background: #ffebee;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #f44336;
    margin: 1rem 0;
    color: #c62828;
}
</style>
""", unsafe_allow_html=True)

def main():
    # 헤더
    st.markdown("""
    <div class="main-header">
        <h1>🎬 AutoAvatar</h1>
        <h3>AI 뉴스 비디오 생성기 (Cloud Edition)</h3>
        <p>이미지와 뉴스 주제로 전문적인 비디오를 자동 생성합니다</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 초기화
    if 'script_generator' not in st.session_state:
        st.session_state.script_generator = ScriptGenerator()
    
    # 사이드바 설정
    with st.sidebar:
        st.markdown("## ⚙️ 설정")
        
        # API 키 설정 버튼
        if st.button("🔑 API 키 설정", key="api_setup_btn"):
            st.session_state.show_api_setup = True
        
        # 음성 설정
        st.markdown("### 🗣️ 음성 설정")
        voice_provider = st.selectbox(
            "음성 제공업체",
            options=["basic"],
            index=0,
            help="Cloud 버전에서는 기본 TTS만 사용 가능합니다"
        )
        
        # 비디오 설정
        st.subheader("🎥 비디오 설정")
        
        duration = st.slider(
            "길이 (초)",
            min_value=15,
            max_value=120,
            value=30,
            step=5,
            help="목표 비디오 길이"
        )
        
        style = st.selectbox(
            "비주얼 스타일",
            options=["Modern", "Classic", "Dramatic"],
            index=0,
            help="비디오의 비주얼 스타일을 선택하세요"
        )
    
    # 메인 콘텐츠
    if st.session_state.get('show_api_setup', False):
        # API 설정 페이지
        render_api_key_setup()
        
        if st.button("⬅️ 메인으로 돌아가기"):
            st.session_state.show_api_setup = False
            st.rerun()
    else:
        # 메인 비디오 생성 인터페이스
        main_tab1, main_tab2 = st.tabs(["🎬 스크립트 생성", "⚙️ API 키 설정"])
        
        with main_tab1:
            # 비디오 생성 인터페이스
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.header("📸 이미지 업로드")
                
                uploaded_file = st.file_uploader(
                    "이미지 파일을 선택하세요",
                    type=['png', 'jpg', 'jpeg', 'bmp', 'tiff'],
                    help="비디오에 사용할 인물 사진이나 이미지를 업로드하세요"
                )
                
                if uploaded_file is not None:
                    # 업로드된 이미지 표시
                    image = Image.open(uploaded_file)
                    st.image(image, caption="업로드된 이미지", use_container_width=True)
            
            with col2:
                st.header("📝 뉴스 주제")
                
                # 예시 주제들
                with st.expander("💡 예시 주제들"):
                    example_topics = [
                        "손흥민 레알 마드리드 이적설",
                        "의료 연구 분야 AI 혁신 기술 발표",
                        "기후변화 정상회의 역사적 합의 도출",
                        "대형 IT 기업 혁신적 스마트폰 발표",
                        "올림픽 관중 동원 기록 경신",
                        "화성 탐사 미션에서 물 발견"
                    ]
                    
                    for i, topic in enumerate(example_topics):
                        if st.button(f"📰 {topic}", key=f"example_topic_{i}"):
                            st.session_state.news_topic = topic
                
                news_topic = st.text_area(
                    "뉴스 제목이나 주제를 입력하세요:",
                    value=st.session_state.get('news_topic', ''),
                    height=100,
                    placeholder="예: '속보: 손흥민 레알 마드리드 영입 확정'",
                    help="스크립트를 생성할 뉴스 주제를 입력하세요"
                )
                
                # 스크립트 생성 버튼
                generate_button = st.button(
                    "📝 스크립트 생성",
                    type="primary",
                    use_container_width=True,
                    disabled=not news_topic.strip(),
                    key="main_generate_btn"
                )
                
                if generate_button:
                    if not news_topic.strip():
                        st.error("뉴스 주제를 입력해주세요!")
                    else:
                        generate_script(news_topic, duration, style)
        
        with main_tab2:
            # API Key setup tab
            render_api_key_setup()

def generate_script(news_topic, duration, style):
    """스크립트 생성"""
    
    # Progress bar and status
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Start generation
    status_text.text("🤖 뉴스 스크립트 생성 중...")
    progress_bar.progress(50)
    
    try:
        # 스크립트 생성
        script = st.session_state.script_generator.generate_news_script(
            topic=news_topic,
            duration_seconds=duration,
            style=style.lower()
        )
        
        progress_bar.progress(100)
        
        if script:
            st.success("🎉 스크립트가 성공적으로 생성되었습니다!")
            
            # 스크립트 표시
            st.markdown("### 📝 생성된 스크립트")
            st.text_area(
                "스크립트 내용:",
                value=script,
                height=300,
                disabled=True
            )
            
            # 타이밍 분석
            timing_info = st.session_state.script_generator.analyze_script_timing(script)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("단어 수", timing_info['word_count'])
            with col2:
                st.metric("예상 길이", f"{timing_info['estimated_duration_seconds']:.1f}초")
            with col3:
                st.metric("말하기 속도", f"{timing_info['words_per_minute']} WPM")
            
            # 다운로드 버튼
            st.download_button(
                label="📥 스크립트 다운로드",
                data=script,
                file_name=f"news_script_{int(time.time())}.txt",
                mime="text/plain"
            )
            
            # Cloud 버전 안내
            st.info("""
            💡 **Cloud 버전 안내**
            
            현재 Streamlit Cloud에서는 다음 기능들이 제한됩니다:
            - 음성 녹음 (마이크 접근 불가)
            - 비디오 생성 (FFmpeg 제한)
            - 고급 TTS (ElevenLabs, Azure)
            
            전체 기능을 사용하려면 로컬에서 실행해주세요.
            """)
        else:
            st.error("❌ 스크립트 생성에 실패했습니다. API 키를 확인해주세요.")
    
    except Exception as e:
        st.error(f"❌ 오류 발생: {str(e)}")
    
    finally:
        status_text.empty()

if __name__ == "__main__":
    main()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>🎬 AutoAvatar - AI 뉴스 비디오 생성기 (Cloud Edition)</p>
        <p>❤️ Streamlit, OpenAI로 제작</p>
    </div>
    """, unsafe_allow_html=True) 