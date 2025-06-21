import streamlit as st
import os
from PIL import Image
import tempfile
import time
from pathlib import Path

from video_generator import AutoVideoGenerator
from config import Config
from utils.config_manager import config_manager
from utils.api_key_ui import render_api_key_setup, show_api_key_status

# Streamlit 페이지 설정
st.set_page_config(
    page_title="AutoAvatar - AI 뉴스 비디오 생성기",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .feature-box {
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    }
    
    .success-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    
    .error-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    
    .info-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: #cce5ff;
        border: 1px solid #99d6ff;
        color: #004085;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # 헤더
    st.markdown('<h1 class="main-header">🎬 AutoAvatar</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">AI 기반 뉴스 비디오 생성기</p>', unsafe_allow_html=True)
    
    # 현재 API 키로 Config 업데이트
    Config.update_from_manager(config_manager)
    
    # API 키 설정 확인
    validation_results = config_manager.validate_api_keys()
    if not validation_results.get('openai', False):
        st.error("🔑 API 키 설정이 필요합니다!")
        render_api_key_setup()
        st.stop()
    
    # 비디오 생성기 초기화
    if 'generator' not in st.session_state:
        try:
            st.session_state.generator = AutoVideoGenerator()
        except Exception as e:
            st.error(f"비디오 생성기 초기화 실패: {e}")
            st.markdown("---")
            render_api_key_setup()
            st.stop()
    
    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 설정")
        
        # API 키 상태
        st.markdown("### 🔑 API 키 상태")
        show_api_key_status()
        
        if st.button("🔧 API 키 설정", key="sidebar_api_setup", help="API 키를 설정하거나 변경합니다"):
            st.session_state.show_api_setup = True
        
        st.markdown("---")
        
        # 시스템 검증
        validation = st.session_state.generator.validate_setup()
        if not validation['valid']:
            st.error("⚠️ 설정 문제:")
            for issue in validation['issues']:
                st.write(f"• {issue}")
            
            with st.expander("📝 설정 안내"):
                st.markdown("""
                **필수 API 키:**
                
                프로젝트 루트에 `.env` 파일 생성:
                ```
                OPENAI_API_KEY=your_openai_key_here
                ELEVENLABS_API_KEY=your_elevenlabs_key_here
                # 또는
                AZURE_SPEECH_KEY=your_azure_key_here
                AZURE_SPEECH_REGION=your_region_here
                ```
                
                **API 키 발급:**
                - OpenAI: https://platform.openai.com/api-keys
                - ElevenLabs: https://elevenlabs.io/
                - Azure Speech: https://azure.microsoft.com/en-us/services/cognitive-services/speech-services/
                """)
        else:
            st.success("✅ 시스템 준비 완료")
        
        # 음성 제공업체 선택
        voice_info = st.session_state.generator.get_available_voices()
        voice_provider = st.selectbox(
            "🎤 음성 제공업체",
            options=voice_info['providers'],
            index=0,
            help="선호하는 텍스트-음성 변환 제공업체를 선택하세요"
        )
        
        # 음성 복제 섹션
        if "cloned" in voice_info['providers']:
            st.subheader("🎭 음성 복제")
            
            voice_cloning_tab1, voice_cloning_tab2, voice_cloning_tab3 = st.tabs([
                "📼 미디어에서", "🎤 음성 녹음", "📁 음성 관리"
            ])
            
            with voice_cloning_tab1:
                st.write("**음성 추출을 위한 비디오/오디오 업로드:**")
                voice_media_file = st.file_uploader(
                    "미디어 파일 선택",
                    type=['mp4', 'avi', 'mov', 'mkv', 'mp3', 'wav', 'flac', 'aac'],
                    help="음성을 추출할 비디오 또는 오디오 파일을 업로드하세요",
                    key="voice_media_uploader"
                )
                
                if voice_media_file is not None:
                    if st.button("🎵 음성 추출", key="extract_voice"):
                        with st.spinner("미디어에서 음성 추출 중..."):
                            # 업로드된 파일 저장
                            temp_media_path = os.path.join(tempfile.gettempdir(), voice_media_file.name)
                            with open(temp_media_path, "wb") as f:
                                f.write(voice_media_file.getbuffer())
                            
                            # 음성 샘플 추출
                            result = st.session_state.generator.create_voice_samples_from_media(temp_media_path)
                            
                            if result.get("success"):
                                st.success(f"✅ 음성 추출 성공!")
                                st.write(f"• **생성된 샘플:** {result['total_samples']}")
                                st.write(f"• **최적 샘플:** {len(result['best_samples'])}")
                                st.write(f"• **세션 ID:** {result['session_id']}")
                                
                                # 세션 정보 저장
                                st.session_state.voice_session_id = result['session_id']
                                st.session_state.voice_samples_dir = result['voice_samples_dir']
                                
                                # 샘플 품질 표시
                                if result.get('best_samples'):
                                    st.write("**샘플 품질:**")
                                    for i, sample in enumerate(result['best_samples'][:3]):
                                        st.write(f"  {i+1}. 길이: {sample['duration']:.1f}초, 품질: {sample['quality']:.2f}")
                            else:
                                st.error(f"❌ 음성 추출 실패: {result.get('error')}")
            
            with voice_cloning_tab2:
                st.write("**직접 음성 녹음:**")
                
                # 마이크 테스트
                if st.button("🎤 마이크 테스트", key="test_mic_btn"):
                    mic_test = st.session_state.generator.test_microphone()
                    if mic_test.get("microphone_working"):
                        st.success(f"✅ 마이크 작동 중! 품질: {mic_test.get('quality', '알 수 없음')}")
                    else:
                        st.error(f"❌ 마이크 문제: {mic_test.get('error', '알 수 없는 오류')}")
                
                # 녹음 설정
                record_duration = st.slider("녹음 시간 (초)", 10, 60, 20)
                
                if st.button("🔴 녹음 시작", key="start_recording_btn"):
                    with st.spinner(f"{record_duration}초 동안 녹음 중..."):
                        import uuid
                        session_id = str(uuid.uuid4())[:8]
                        recorded_path = os.path.join(Config.TEMP_DIR, f"recorded_voice_{session_id}.wav")
                        
                        # 음성 녹음
                        record_result = st.session_state.generator.record_voice_from_microphone(
                            duration=record_duration,
                            output_path=recorded_path
                        )
                        
                        if record_result.get("success"):
                            st.success("✅ 녹음 완료!")
                            
                            # 녹음에서 음성 샘플 생성
                            samples_result = st.session_state.generator.tts_engine.create_voice_samples(
                                recorded_path, 
                                os.path.join(Config.TEMP_DIR, f"voice_samples_{session_id}")
                            )
                            
                            if samples_result.get("success"):
                                st.write(f"• **품질 점수:** {record_result['quality_score']:.2f}")
                                st.write(f"• **생성된 샘플:** {samples_result['total_samples']}")
                                
                                # 세션 정보 저장
                                st.session_state.voice_session_id = session_id
                                st.session_state.voice_samples_dir = samples_result['output_dir']
                            else:
                                st.error("녹음에서 음성 샘플 생성 실패")
                        else:
                            st.error(f"❌ 녹음 실패: {record_result.get('error')}")
            
            with voice_cloning_tab3:
                st.write("**현재 음성 세션:**")
                
                if hasattr(st.session_state, 'voice_session_id'):
                    st.info(f"🎭 활성 음성 세션: {st.session_state.voice_session_id}")
                    
                    if st.button("🗑️ 음성 세션 삭제", key="clear_voice_session_btn"):
                        if hasattr(st.session_state, 'voice_samples_dir'):
                            # 음성 샘플 정리
                            try:
                                import shutil
                                shutil.rmtree(st.session_state.voice_samples_dir)
                            except:
                                pass
                        
                        # 세션 변수 삭제
                        delattr(st.session_state, 'voice_session_id')
                        if hasattr(st.session_state, 'voice_samples_dir'):
                            delattr(st.session_state, 'voice_samples_dir')
                        
                        st.success("음성 세션이 삭제되었습니다!")
                        st.rerun()
                else:
                    st.write("활성 음성 세션이 없습니다")
        
        # 복제된 음성 사용 안내
        if hasattr(st.session_state, 'voice_session_id') and voice_provider != "cloned":
            st.info("💡 복제된 음성을 사용할 수 있습니다! 음성 제공업체를 'cloned'로 설정하세요.")
        
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
        
        # 고급 옵션
        with st.expander("🔧 고급 옵션"):
            show_script = st.checkbox("생성된 스크립트 표시", value=True)
            show_timing = st.checkbox("타이밍 분석 표시", value=True)
            auto_cleanup = st.checkbox("오래된 파일 자동 정리", value=True)
            
            if auto_cleanup:
                cleanup_days = st.number_input("다음보다 오래된 파일 정리 (일)", min_value=1, max_value=30, value=7)
    
    # Main content area with tabs
    if st.session_state.get('show_api_setup', False):
        # Show API setup page
        render_api_key_setup()
        
        if st.button("⬅️ 메인으로 돌아가기"):
            st.session_state.show_api_setup = False
            st.rerun()
    else:
        # 메인 비디오 생성 인터페이스
        main_tab1, main_tab2, main_tab3 = st.tabs(["🎬 비디오 생성", "⚙️ API 키 설정", "📁 파일 관리"])
        
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
            
            # Save uploaded file temporarily
            temp_dir = tempfile.mkdtemp()
            temp_image_path = os.path.join(temp_dir, uploaded_file.name)
            
            with open(temp_image_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.session_state.temp_image_path = temp_image_path
            
            # 배경음악 업로드
            st.subheader("🎵 배경음악 (선택사항)")
            music_file = st.file_uploader(
                "배경음악을 선택하세요",
                type=['mp3', 'wav', 'aac'],
                help="비디오에 사용할 배경음악을 업로드하세요 (선택사항)"
            )
            
            if music_file is not None:
                temp_music_path = os.path.join(temp_dir, music_file.name)
                with open(temp_music_path, "wb") as f:
                    f.write(music_file.getbuffer())
                st.session_state.temp_music_path = temp_music_path
                st.success("🎵 배경음악이 업로드되었습니다!")

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
                    help="비디오로 만들고 싶은 뉴스 주제를 입력하세요"
                )
                
                # 생성 버튼
                generate_button = st.button(
                    "🚀 비디오 생성",
                    type="primary",
                    use_container_width=True,
                    disabled=not (uploaded_file and news_topic.strip()),
                    key="main_generate_btn"
                )
                
                if generate_button:
                    if not hasattr(st.session_state, 'temp_image_path'):
                        st.error("먼저 이미지를 업로드해주세요!")
                    elif not news_topic.strip():
                        st.error("뉴스 주제를 입력해주세요!")
                    else:
                        # 복제된 음성 사용 시 음성 샘플 디렉토리 가져오기
                        voice_samples_dir = None
                        if voice_provider == "cloned" and hasattr(st.session_state, 'voice_samples_dir'):
                            voice_samples_dir = st.session_state.voice_samples_dir
                        
                        generate_video(
                            st.session_state.temp_image_path,
                            news_topic,
                            duration,
                            style.lower(),
                            voice_provider,
                            st.session_state.get('temp_music_path', None),
                            voice_samples_dir,
                            show_script,
                            show_timing
                        )
        
        with main_tab2:
            # API Key setup tab
            render_api_key_setup()
        
        with main_tab3:
            # File management tab
            show_file_management()

def generate_video(image_path, news_topic, duration, style, voice_provider, music_path, voice_samples_dir, show_script, show_timing):
    """Generate video with progress tracking"""
    
    # Progress bar and status
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Start generation
    status_text.text("🤖 Generating news script...")
    progress_bar.progress(10)
    
    with st.spinner("Creating your video..."):
        result = st.session_state.generator.generate_video(
            image_path=image_path,
            news_topic=news_topic,
            duration=duration,
            style=style,
            voice_provider=voice_provider,
            background_music_path=music_path,
            voice_samples_dir=voice_samples_dir
        )
    
    progress_bar.progress(100)
    
    if result['success']:
        st.success("🎉 Video generated successfully!")
        
        # Display results
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Video player
            video_file = open(result['video_path'], 'rb')
            video_bytes = video_file.read()
            st.video(video_bytes)
            
            # Download button
            st.download_button(
                label="📥 Download Video",
                data=video_bytes,
                file_name=f"news_video_{int(time.time())}.mp4",
                mime="video/mp4"
            )
        
        with col2:
            # Video info
            video_info = st.session_state.generator.get_video_info(result['video_path'])
            
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.write("**📊 Video Information:**")
            st.write(f"• Duration: {result['actual_duration']:.1f}s")
            st.write(f"• File size: {video_info['size_mb']} MB")
            st.write(f"• Style: {result['style'].title()}")
            st.write(f"• Voice: {result['voice_provider'].title()}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Script display
            if show_script and result.get('script'):
                with st.expander("📝 Generated Script"):
                    st.text_area("Script", value=result['script'], height=200, disabled=True)
            
            # Timing analysis
            if show_timing and result.get('timing_info'):
                with st.expander("⏱️ Timing Analysis"):
                    timing = result['timing_info']
                    st.write(f"**Word count:** {timing['word_count']}")
                    st.write(f"**Estimated duration:** {timing['estimated_duration_seconds']}s")
                    st.write(f"**Actual duration:** {result['actual_duration']:.1f}s")
                    st.write(f"**Speaking rate:** {timing['words_per_minute']} WPM")
    
    else:
        st.markdown(f'<div class="error-box">❌ Error: {result["error"]}</div>', unsafe_allow_html=True)
    
    status_text.empty()

# Additional features section
def show_additional_features():
    st.header("🔧 Additional Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="feature-box">', unsafe_allow_html=True)
        st.subheader("🎨 Styles Available")
        st.write("• **Modern**: Clean gradients, subtle animations")
        st.write("• **Classic**: Professional, traditional news look")
        st.write("• **Dramatic**: Bold colors, dynamic effects")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="feature-box">', unsafe_allow_html=True)
        st.subheader("🗣️ Voice Options")
        st.write("• **Voice Cloning**: Extract from video/audio files")
        st.write("• **Microphone Recording**: Record your own voice")
        st.write("• **ElevenLabs**: Premium AI voices")
        st.write("• **Azure**: Microsoft's speech service")
        st.write("• **Basic**: Fallback TTS option")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="feature-box">', unsafe_allow_html=True)
        st.subheader("⚡ Quick Features")
        st.write("• Auto script generation")
        st.write("• Dynamic subtitles")
        st.write("• Background music mixing")
        st.write("• Multiple export formats")
        st.markdown('</div>', unsafe_allow_html=True)

# File management section
def show_file_management():
    st.markdown("### 📁 파일 관리")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧹 오래된 파일 정리", key="cleanup_files_btn"):
            if 'generator' in st.session_state:
                cleaned = st.session_state.generator.cleanup_old_files()
                if cleaned:
                    st.success(f"{len(cleaned)}개의 오래된 파일을 정리했습니다")
                else:
                    st.info("정리할 오래된 파일이 없습니다")
            else:
                st.warning("비디오 생성기가 초기화되지 않았습니다")
    
    with col2:
        # 출력 디렉토리 내용 표시
        output_dir = Config.OUTPUT_DIR
        if os.path.exists(output_dir):
            files = [f for f in os.listdir(output_dir) if f.endswith('.mp4')]
            st.write(f"**출력 폴더의 비디오:** {len(files)}개")
        else:
            st.write("**출력 폴더:** 아직 생성되지 않음")

if __name__ == "__main__":
    main()
    
    # Additional sections
    st.markdown("---")
    show_additional_features()
    show_file_management()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>🎬 AutoAvatar - AI News Video Generator</p>
        <p>Created with ❤️ using Streamlit, OpenAI, and MoviePy</p>
    </div>
    """, unsafe_allow_html=True) 