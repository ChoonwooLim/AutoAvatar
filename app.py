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
                
                # 마이크 테스트 및 볼륨 모니터링
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🎤 마이크 테스트", key="test_mic_btn"):
                        current_mic = st.session_state.get('current_mic_index', None)
                        
                        with st.spinner("마이크를 테스트하는 중..."):
                            mic_test = st.session_state.generator.test_microphone(current_mic)
                        
                        if mic_test.get("microphone_working"):
                            st.success(f"✅ 마이크 작동 중! 품질: {mic_test.get('quality', '알 수 없음')}")
                            if mic_test.get('audio_level'):
                                st.info(f"🔊 오디오 레벨: {mic_test.get('audio_level', 0):.0f}")
                        else:
                            error_msg = mic_test.get('error', '알 수 없는 오류')
                            st.error(f"❌ 마이크 문제: {error_msg}")
                            
                            # 마이크 테스트 실패 시 해결 방법 제시
                            if "Unanticipated host error" in error_msg or "-9999" in error_msg:
                                st.warning("""
                                **🔧 마이크 문제 해결:**
                                1. **다른 마이크 선택**: 아래에서 다른 마이크 선택
                                2. **권한 확인**: 브라우저에서 마이크 접근 권한 허용
                                3. **기본 마이크 사용**: Windows 설정에서 기본 마이크로 설정
                                4. **앱 재시작**: 브라우저 새로고침 후 다시 시도
                                """)
                            elif "Cannot open microphone" in error_msg:
                                st.info("""
                                **💡 추가 확인사항:**
                                - 마이크가 다른 앱에서 사용 중인지 확인
                                - USB 마이크인 경우 연결 상태 확인
                                - 시스템 사운드 설정에서 마이크 활성화 확인
                                """)
                
                with col2:
                    # 실시간 볼륨 모니터링 토글
                    if 'audio_monitoring' not in st.session_state:
                        st.session_state.audio_monitoring = False
                    if 'audio_level_data' not in st.session_state:
                        st.session_state.audio_level_data = {'rms_level': 0, 'peak_level': 0, 'clipping': False}
                    
                    if st.button("📊 볼륨 모니터링", key="volume_monitor_btn"):
                        if not st.session_state.audio_monitoring:
                            # 모니터링 시작 (콜백 없이)
                            current_gain = st.session_state.get('current_gain', 1.0)
                            current_mic = st.session_state.get('current_mic_index', None)
                            
                            with st.spinner("오디오 모니터링을 시작하는 중..."):
                                result = st.session_state.generator.start_audio_monitoring(
                                    device_index=current_mic,
                                    gain_multiplier=current_gain
                                )
                            
                            if result.get("success"):
                                st.session_state.audio_monitoring = True
                                st.success("🎙️ 볼륨 모니터링 시작")
                            else:
                                error_msg = result.get('error', '알 수 없는 오류')
                                st.error(f"❌ 모니터링 시작 실패: {error_msg}")
                                
                                # 구체적인 해결 방법 제시
                                if "Unanticipated host error" in error_msg or "-9999" in error_msg:
                                    st.warning("""
                                    **🔧 해결 방법:**
                                    1. 다른 마이크를 선택해보세요
                                    2. 시스템 오디오 설정에서 마이크 권한 확인
                                    3. 브라우저를 새로고침 후 다시 시도
                                    4. 시스템 기본 마이크로 변경 후 재시도
                                    """)
                                elif "Cannot open audio stream" in error_msg:
                                    st.info("""
                                    **💡 권장사항:**
                                    - 시스템 기본 마이크 사용 권장
                                    - 다른 앱에서 마이크 사용 중인지 확인
                                    - 마이크 목록을 새로고침해보세요
                                    """)
                        else:
                            # 모니터링 중지
                            st.session_state.generator.stop_audio_monitoring()
                            st.session_state.audio_monitoring = False
                            st.session_state.audio_level_data = {'rms_level': 0, 'peak_level': 0, 'clipping': False}
                            st.info("🔇 볼륨 모니터링 중지")
                            st.rerun()
                
                # 실시간 볼륨 표시창
                if st.session_state.audio_monitoring:
                    st.markdown("### 🎚️ 실시간 오디오 레벨")
                    
                    # 오디오 레벨 데이터 가져오기 (새로운 방식)
                    level_data = st.session_state.generator.get_current_audio_level()
                    rms_level = level_data.get('rms_level', 0)
                    peak_level = level_data.get('peak_level', 0)
                    clipping = level_data.get('clipping', False)
                    
                    # RMS 레벨 바
                    rms_percentage = min(100, rms_level * 100)
                    rms_color = "red" if clipping else "orange" if rms_percentage > 80 else "green"
                    
                    st.markdown(f"""
                    <div style="margin: 10px 0;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                            <span><strong>🎤 RMS 레벨</strong></span>
                            <span style="color: {'red' if clipping else 'inherit'};">
                                {rms_percentage:.1f}% {'🚨 CLIP!' if clipping else ''}
                            </span>
                        </div>
                        <div style="
                            width: 100%;
                            height: 25px;
                            background: #ddd;
                            border-radius: 12px;
                            overflow: hidden;
                            border: 2px solid {'red' if clipping else '#ccc'};
                        ">
                            <div style="
                                width: {rms_percentage}%;
                                height: 100%;
                                background: linear-gradient(90deg, {rms_color}, {rms_color});
                                transition: width 0.1s ease;
                                border-radius: 10px;
                            "></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 피크 레벨 바
                    peak_percentage = min(100, peak_level * 100)
                    peak_color = "red" if peak_percentage > 95 else "orange" if peak_percentage > 80 else "green"
                    
                    st.markdown(f"""
                    <div style="margin: 10px 0;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                            <span><strong>📈 피크 레벨</strong></span>
                            <span>{peak_percentage:.1f}%</span>
                        </div>
                        <div style="
                            width: 100%;
                            height: 20px;
                            background: #ddd;
                            border-radius: 10px;
                            overflow: hidden;
                        ">
                            <div style="
                                width: {peak_percentage}%;
                                height: 100%;
                                background: {peak_color};
                                transition: width 0.1s ease;
                                border-radius: 8px;
                            "></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 상태 표시
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        signal_quality = "좋음" if rms_level > 0.1 else "보통" if rms_level > 0.01 else "낮음"
                        quality_color = "green" if rms_level > 0.1 else "orange" if rms_level > 0.01 else "red"
                        st.markdown(f"**신호 품질:** <span style='color: {quality_color}'>{signal_quality}</span>", unsafe_allow_html=True)
                    
                    with col2:
                        gain_status = f"{level_data.get('gain', 1.0):.1f}x"
                        st.markdown(f"**적용된 게인:** {gain_status}")
                    
                    with col3:
                        if clipping:
                            st.markdown("**상태:** <span style='color: red'>⚠️ 클리핑</span>", unsafe_allow_html=True)
                        elif rms_level > 0.05:
                            st.markdown("**상태:** <span style='color: green'>✅ 정상</span>", unsafe_allow_html=True)
                        else:
                            st.markdown("**상태:** <span style='color: orange'>🔇 조용함</span>", unsafe_allow_html=True)
                    
                    # 자동 새로고침 (모니터링 중일 때만)
                    time.sleep(0.1)
                    st.rerun()
                
                # 녹음 설정
                col1, col2 = st.columns(2)
                with col1:
                    record_duration = st.slider("녹음 시간 (초)", 10, 60, 20)
                with col2:
                    gain_multiplier = st.slider(
                        "입력 게인 (배율)", 
                        min_value=0.1, 
                        max_value=5.0, 
                        value=1.0, 
                        step=0.1,
                        help="마이크 입력 음량을 조정합니다. 1.0이 기본값입니다."
                    )
                    # 세션 상태에 저장
                    st.session_state.current_gain = gain_multiplier
                
                # 게인 레벨 표시 및 실시간 반영
                if gain_multiplier < 0.5:
                    st.info("🔉 낮은 게인: 조용한 환경에서 사용")
                elif gain_multiplier > 2.0:
                    st.warning("🔊 높은 게인: 노이즈가 증가할 수 있습니다")
                else:
                    st.success("🔊 적정 게인: 권장 설정")
                
                # 게인 변경 시 모니터링 업데이트
                if st.session_state.audio_monitoring:
                    # 현재 게인과 저장된 게인이 다르면 모니터링 재시작
                    if 'last_gain' not in st.session_state:
                        st.session_state.last_gain = gain_multiplier
                    elif abs(st.session_state.last_gain - gain_multiplier) > 0.1:
                        st.session_state.last_gain = gain_multiplier
                        # 모니터링 재시작 (콜백 없이)
                        st.session_state.generator.stop_audio_monitoring()
                        
                        st.session_state.generator.start_audio_monitoring(
                            device_index=st.session_state.get('current_mic_index', None),
                            gain_multiplier=gain_multiplier
                        )
                
                # 🎙️ 오디오 입력 소스 선택 (메인 화면으로 이동)
                st.markdown("### 🎙️ 오디오 입력 소스")
                
                available_mics = st.session_state.generator.get_available_microphones()
                if available_mics:
                    # 마이크 정보 표시
                    st.info(f"📊 **{len(available_mics)}개**의 오디오 입력 장치를 발견했습니다")
                    
                    # 마이크 선택 드롭다운
                    mic_options = ["🎤 기본 마이크 (시스템 기본값)"] + [f"🎙️ {mic['name']}" for mic in available_mics]
                    selected_mic = st.selectbox(
                        "사용할 마이크를 선택하세요:",
                        mic_options,
                        help="마이크를 변경하면 볼륨 모니터링이 자동으로 재시작됩니다"
                    )
                    
                    if selected_mic.startswith("🎤 기본 마이크"):
                        selected_mic_index = None
                        current_mic_name = "시스템 기본 마이크"
                    else:
                        mic_name = selected_mic.replace("🎙️ ", "")
                        selected_mic_index = next(
                            (i for i, mic in enumerate(available_mics) 
                             if mic['name'] == mic_name), None
                        )
                        current_mic_name = mic_name
                    
                    # 세션 상태에 저장
                    old_mic_index = st.session_state.get('current_mic_index', None)
                    st.session_state.current_mic_index = selected_mic_index
                    
                    # 마이크 변경시 모니터링 재시작
                    if old_mic_index != selected_mic_index and st.session_state.audio_monitoring:
                        st.session_state.generator.stop_audio_monitoring()
                        st.session_state.generator.start_audio_monitoring(
                            device_index=selected_mic_index,
                            gain_multiplier=st.session_state.get('current_gain', 1.0)
                        )
                        st.success(f"🔄 마이크가 '{current_mic_name}'로 변경되었습니다!")
                    
                    # 현재 선택된 마이크 표시
                    st.success(f"✅ **현재 마이크:** {current_mic_name}")
                    
                    # 마이크 상세 정보 (확장 메뉴)
                    with st.expander("📋 마이크 상세 정보", expanded=False):
                        if selected_mic_index is not None and selected_mic_index < len(available_mics):
                            mic_info = available_mics[selected_mic_index]
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**장치명:** {mic_info.get('name', 'N/A')}")
                                st.write(f"**인덱스:** {selected_mic_index}")
                            with col2:
                                st.write(f"**채널 수:** {mic_info.get('maxInputChannels', 'N/A')}")
                                st.write(f"**샘플레이트:** {mic_info.get('defaultSampleRate', 'N/A')} Hz")
                        else:
                            st.write("**시스템 기본 마이크 사용 중**")
                            st.write("상세 정보는 시스템 설정에서 확인하세요.")
                
                else:
                    st.error("❌ 사용 가능한 마이크를 찾을 수 없습니다!")
                    st.info("""
                    **해결 방법:**
                    1. 마이크가 컴퓨터에 연결되어 있는지 확인
                    2. 시스템 오디오 설정에서 마이크 권한 확인
                    3. 브라우저에서 마이크 접근 권한 허용
                    4. 앱을 새로고침하여 다시 시도
                    """)
                    # 세션 상태에 저장
                    st.session_state.current_mic_index = None
                
                # 고급 설정 (간소화)
                with st.expander("⚙️ 고급 설정", expanded=False):
                    # 빠른 레벨 체크
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("⚡ 빠른 레벨 체크", key="quick_level_check", use_container_width=True):
                            with st.spinner("오디오 레벨 확인 중..."):
                                level_check = st.session_state.generator.get_audio_level_preview(
                                    device_index=st.session_state.get('current_mic_index', None),
                                    gain_multiplier=st.session_state.get('current_gain', 1.0),
                                    duration=1.0
                                )
                                
                                if level_check.get("success"):
                                    rms = level_check.get("rms_level", 0)
                                    peak = level_check.get("peak_level", 0)
                                    quality = level_check.get("signal_quality", "알 수 없음")
                                    clipping = level_check.get("clipping_detected", False)
                                    
                                    st.success("✅ 레벨 체크 완료!")
                                    metric_col1, metric_col2 = st.columns(2)
                                    with metric_col1:
                                        st.metric("RMS 레벨", f"{rms*100:.1f}%")
                                        st.metric("신호 품질", quality)
                                    with metric_col2:
                                        st.metric("피크 레벨", f"{peak*100:.1f}%")
                                        if clipping:
                                            st.error("⚠️ 클리핑 감지됨!")
                                        else:
                                            st.success("✅ 클리핑 없음")
                                else:
                                    error_msg = level_check.get('error', '알 수 없는 오류')
                                    st.error(f"❌ 레벨 체크 실패: {error_msg}")
                                    
                                    # 상세한 오류 분석 및 해결 방법
                                    if "Cannot open audio stream" in error_msg:
                                        with st.expander("🔧 오류 해결 방법", expanded=True):
                                            st.warning("""
                                            **오디오 스트림 생성 실패 해결 방법:**
                                            
                                            1. **마이크 선택 변경**
                                               - 위의 드롭다운에서 다른 마이크 선택
                                               - 시스템 기본 마이크 사용 권장
                                            
                                            2. **마이크 권한 확인**
                                               - Windows 설정 → 개인정보 → 마이크
                                               - 브라우저 마이크 권한 허용
                                            
                                            3. **마이크 상태 확인**
                                               - 다른 앱에서 마이크 사용 중인지 확인
                                               - USB 마이크인 경우 연결 상태 확인
                                            
                                            4. **시스템 재시작**
                                               - 오디오 드라이버 문제일 수 있음
                                               - 앱 새로고침 또는 브라우저 재시작
                                            """)
                                            
                                            # 구체적인 오류 정보 표시
                                            if "Last error:" in error_msg:
                                                st.info(f"**구체적인 오류:** {error_msg}")
                                    
                                    # 대안 제시
                                    st.info("""
                                    **💡 대안:**
                                    - 마이크 테스트 버튼을 먼저 시도해보세요
                                    - 볼륨 모니터링으로 실시간 확인 가능
                                    - 녹음 기능은 별도로 작동할 수 있습니다
                                    """)
                    
                    with col2:
                        if st.button("🔄 마이크 목록 새로고침", key="refresh_mics", use_container_width=True):
                            st.rerun()
                
                # 녹음 상태 초기화
                if 'recording_state' not in st.session_state:
                    st.session_state.recording_state = 'idle'  # idle, recording, processing
                if 'recording_start_time' not in st.session_state:
                    st.session_state.recording_start_time = None
                if 'recording_process' not in st.session_state:
                    st.session_state.recording_process = None
                if 'recording_progress_data' not in st.session_state:
                    st.session_state.recording_progress_data = None
                
                # 녹음 상태에 따른 UI
                if st.session_state.recording_state == 'idle':
                    # 녹음 시작 버튼
                    if st.button("🔴 녹음 시작", key="start_recording_btn"):
                        st.session_state.recording_state = 'recording'
                        st.session_state.recording_start_time = time.time()
                        st.rerun()
                
                elif st.session_state.recording_state == 'recording':
                    # 녹음 중 상태 표시
                    elapsed_time = time.time() - st.session_state.recording_start_time
                    remaining_time = max(0, record_duration - elapsed_time)
                    
                    # 진행 상황 표시
                    progress = min(elapsed_time / record_duration, 1.0)
                    
                    # 녹음 상태 표시 박스
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(90deg, #ff4444, #ff6666);
                        color: white;
                        padding: 1rem;
                        border-radius: 10px;
                        text-align: center;
                        margin: 1rem 0;
                        animation: pulse 2s infinite;
                    ">
                        <h3>🔴 녹음 중... (게인: {gain_multiplier:.1f}x)</h3>
                    </div>
                    <style>
                    @keyframes pulse {{
                        0% {{ opacity: 1; }}
                        50% {{ opacity: 0.7; }}
                        100% {{ opacity: 1; }}
                    }}
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # 향상된 진행률 표시
                    progress_col1, progress_col2 = st.columns([3, 1])
                    
                    with progress_col1:
                        st.progress(progress, text=f"진행률: {progress*100:.1f}% | {elapsed_time:.1f}s / {record_duration}s")
                    
                    with progress_col2:
                        # 실시간 오디오 레벨 표시 (시뮬레이션)
                        if st.session_state.recording_progress_data:
                            audio_level = st.session_state.recording_progress_data.get('audio_level', 0)
                            level_percentage = min(100, audio_level * 100)
                            
                            # 오디오 레벨 바
                            level_color = "green" if level_percentage < 70 else "orange" if level_percentage < 90 else "red"
                            st.markdown(f"""
                            <div style="text-align: center;">
                                <small>음성 레벨</small><br>
                                <div style="
                                    width: 100%;
                                    height: 20px;
                                    background: #ddd;
                                    border-radius: 10px;
                                    overflow: hidden;
                                ">
                                    <div style="
                                        width: {level_percentage}%;
                                        height: 100%;
                                        background: {level_color};
                                        transition: width 0.1s;
                                    "></div>
                                </div>
                                <small>{level_percentage:.0f}%</small>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # 상세 정보 표시
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("경과 시간", f"{elapsed_time:.1f}초")
                    with col2:
                        st.metric("남은 시간", f"{remaining_time:.1f}초")
                    with col3:
                        if st.session_state.recording_progress_data:
                            gain_status = "🔊 정상" if gain_multiplier <= 2.0 else "⚠️ 높음"
                            st.metric("게인 상태", gain_status)
                    
                    # 실시간 오디오 통계 (있는 경우)
                    if st.session_state.recording_progress_data:
                        with st.expander("📊 실시간 오디오 통계", expanded=False):
                            data = st.session_state.recording_progress_data
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**오디오 레벨:** {data.get('audio_level', 0):.3f}")
                                st.write(f"**적용된 게인:** {data.get('gain', 1.0):.1f}x")
                            with col2:
                                st.write(f"**진행률:** {data.get('progress', 0)*100:.1f}%")
                                if data.get('audio_level', 0) > 0.9:
                                    st.warning("⚠️ 오디오 레벨이 높습니다!")
                    
                    # 정지 버튼 (크고 눈에 띄게)
                    if st.button("⏹️ 녹음 정지", key="stop_recording_btn", type="secondary", use_container_width=True):
                        st.session_state.recording_state = 'processing'
                        st.rerun()
                    
                    # 자동 정지 (시간 초과)
                    if elapsed_time >= record_duration:
                        st.session_state.recording_state = 'processing'
                        st.rerun()
                    
                    # 실시간 업데이트를 위한 자동 새로고침
                    if remaining_time > 0:
                        time.sleep(0.3)  # 0.3초마다 업데이트 (더 부드러운 UI)
                        st.rerun()
                
                elif st.session_state.recording_state == 'processing':
                    # 녹음 처리 중
                    with st.spinner("녹음을 처리하고 음성 샘플을 생성하는 중..."):
                        import uuid
                        session_id = str(uuid.uuid4())[:8]
                        recorded_path = os.path.join(Config.TEMP_DIR, f"recorded_voice_{session_id}.wav")
                        
                        # 실제 녹음 시간 계산
                        actual_duration = min(time.time() - st.session_state.recording_start_time, record_duration)
                        
                        # 프로그레스 콜백 함수 정의
                        def progress_callback(data):
                            st.session_state.recording_progress_data = data
                        
                        # 음성 녹음 (게인 조정과 프로그레스 콜백 포함)
                        record_result = st.session_state.generator.record_voice_from_microphone(
                            duration=int(actual_duration),
                            output_path=recorded_path,
                            gain_multiplier=st.session_state.get('current_gain', 1.0),
                            device_index=st.session_state.get('current_mic_index', None),
                            progress_callback=progress_callback
                        )
                        
                        if record_result.get("success"):
                            st.success(f"✅ 녹음 완료! ({actual_duration:.1f}초)")
                            
                            # 녹음에서 음성 샘플 생성
                            samples_result = st.session_state.generator.tts_engine.create_voice_samples(
                                recorded_path, 
                                os.path.join(Config.TEMP_DIR, f"voice_samples_{session_id}")
                            )
                            
                            if samples_result.get("success"):
                                # 녹음 결과 통계 표시
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("품질 점수", f"{record_result.get('quality_score', 0):.2f}")
                                with col2:
                                    st.metric("생성된 샘플", samples_result['total_samples'])
                                with col3:
                                    st.metric("녹음 길이", f"{actual_duration:.1f}초")
                                
                                # 오디오 통계 (있는 경우)
                                audio_stats = record_result.get('audio_stats', {})
                                if audio_stats:
                                    with st.expander("📊 상세 오디오 분석", expanded=True):
                                        stat_col1, stat_col2 = st.columns(2)
                                        with stat_col1:
                                            st.write(f"**RMS 레벨:** {audio_stats.get('rms_level', 0):.3f}")
                                            st.write(f"**피크 레벨:** {audio_stats.get('peak_level', 0):.3f}")
                                            st.write(f"**적용된 게인:** {record_result.get('gain_applied', 1.0):.1f}x")
                                        with stat_col2:
                                            st.write(f"**다이나믹 레인지:** {audio_stats.get('dynamic_range', 0):.2f}")
                                            st.write(f"**주요 주파수:** {audio_stats.get('dominant_frequency', 0):.0f} Hz")
                                            
                                            if audio_stats.get('clipping_detected', False):
                                                st.error("⚠️ 클리핑 감지됨 - 게인을 낮춰주세요")
                                            else:
                                                st.success("✅ 클리핑 없음")
                                
                                # 세션 정보 저장
                                st.session_state.voice_session_id = session_id
                                st.session_state.voice_samples_dir = samples_result['output_dir']
                                
                                # 오디오 플레이어 추가
                                if os.path.exists(recorded_path):
                                    st.audio(recorded_path, format="audio/wav")
                            else:
                                st.error("녹음에서 음성 샘플 생성 실패")
                        else:
                            st.error(f"❌ 녹음 실패: {record_result.get('error', '알 수 없는 오류')}")
                    
                    # 상태 초기화
                    st.session_state.recording_state = 'idle'
                    st.session_state.recording_start_time = None
                    
                    # 새 녹음 버튼
                    if st.button("🔄 새로 녹음하기", key="new_recording_btn"):
                        st.session_state.recording_state = 'idle'
                        st.rerun()
            
            with voice_cloning_tab3:
                st.markdown("### 🎭 음성 샘플 관리")
                
                # 현재 활성 세션 표시
                if hasattr(st.session_state, 'voice_session_id'):
                    st.success(f"✅ 활성 음성 세션: **{st.session_state.voice_session_id}**")
                    
                    # 음성 샘플 확인 및 재생
                    if hasattr(st.session_state, 'voice_samples_dir') and os.path.exists(st.session_state.voice_samples_dir):
                        st.markdown("#### 🎵 생성된 음성 샘플")
                        
                        # 샘플 파일 목록 가져오기
                        sample_files = []
                        for filename in os.listdir(st.session_state.voice_samples_dir):
                            if filename.endswith('.wav'):
                                sample_path = os.path.join(st.session_state.voice_samples_dir, filename)
                                if os.path.exists(sample_path):
                                    # 파일 크기와 길이 정보
                                    file_size = os.path.getsize(sample_path) / 1024  # KB
                                    try:
                                        import librosa
                                        audio, sr = librosa.load(sample_path, sr=None)
                                        duration = len(audio) / sr
                                    except:
                                        duration = 0
                                    
                                    sample_files.append({
                                        'name': filename,
                                        'path': sample_path,
                                        'size': file_size,
                                        'duration': duration
                                    })
                        
                        if sample_files:
                            # 샘플 정보 표시
                            st.info(f"📊 총 **{len(sample_files)}개**의 음성 샘플이 생성되었습니다")
                            
                            # 각 샘플 표시
                            for i, sample in enumerate(sample_files):
                                with st.expander(f"🎤 {sample['name']} ({sample['duration']:.1f}초, {sample['size']:.1f}KB)", expanded=False):
                                    col1, col2 = st.columns([3, 1])
                                    
                                    with col1:
                                        # 오디오 플레이어
                                        st.audio(sample['path'], format="audio/wav")
                                    
                                    with col2:
                                        # 샘플 정보
                                        st.metric("길이", f"{sample['duration']:.1f}초")
                                        st.metric("크기", f"{sample['size']:.1f}KB")
                                        
                                        # 품질 평가 (간단한 휴리스틱)
                                        if sample['duration'] >= 3.0:
                                            quality = "좋음" if sample['duration'] <= 10.0 else "길음"
                                            quality_color = "green" if quality == "좋음" else "orange"
                                        else:
                                            quality = "짧음"
                                            quality_color = "red"
                                        
                                        st.markdown(f"**품질:** <span style='color: {quality_color}'>{quality}</span>", unsafe_allow_html=True)
                            
                            # 샘플 통계
                            st.markdown("#### 📈 샘플 통계")
                            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                            
                            total_duration = sum(s['duration'] for s in sample_files)
                            total_size = sum(s['size'] for s in sample_files)
                            good_samples = len([s for s in sample_files if 3.0 <= s['duration'] <= 10.0])
                            
                            with stat_col1:
                                st.metric("총 샘플 수", len(sample_files))
                            with stat_col2:
                                st.metric("총 길이", f"{total_duration:.1f}초")
                            with stat_col3:
                                st.metric("총 크기", f"{total_size:.1f}KB")
                            with stat_col4:
                                st.metric("품질 좋은 샘플", f"{good_samples}개")
                        else:
                            st.warning("⚠️ 음성 샘플이 생성되지 않았습니다. 더 긴 음성이나 명확한 발음의 오디오를 사용해보세요.")
                    else:
                        st.warning("⚠️ 음성 샘플 폴더를 찾을 수 없습니다.")
                    
                    # 세션 관리 버튼들
                    st.markdown("#### ⚙️ 세션 관리")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("🔄 샘플 새로고침", key="refresh_samples_btn", use_container_width=True):
                            st.rerun()
                    
                    with col2:
                        if st.button("🗑️ 음성 세션 삭제", key="clear_voice_session_btn", use_container_width=True):
                            if hasattr(st.session_state, 'voice_samples_dir'):
                                # 음성 샘플 정리
                                try:
                                    import shutil
                                    shutil.rmtree(st.session_state.voice_samples_dir)
                                    st.success("✅ 음성 샘플 폴더가 삭제되었습니다!")
                                except Exception as e:
                                    st.error(f"폴더 삭제 실패: {e}")
                            
                            # 세션 변수 삭제
                            delattr(st.session_state, 'voice_session_id')
                            if hasattr(st.session_state, 'voice_samples_dir'):
                                delattr(st.session_state, 'voice_samples_dir')
                            
                            st.success("🎭 음성 세션이 삭제되었습니다!")
                            st.rerun()
                
                else:
                    st.info("💡 현재 활성 음성 세션이 없습니다")
                    st.markdown("""
                    **음성 샘플을 생성하려면:**
                    1. 📁 **미디어에서** 탭: 비디오/오디오 파일 업로드
                    2. 🎤 **음성 녹음** 탭: 마이크로 직접 녹음
                    """)
                
                # 모든 세션 관리 (고급 기능)
                with st.expander("🔧 고급: 모든 음성 세션 관리", expanded=False):
                    st.markdown("#### 📁 저장된 모든 음성 세션")
                    
                    # temp 폴더에서 voice_samples_ 폴더들 찾기
                    all_sessions = []
                    if os.path.exists(Config.TEMP_DIR):
                        for item in os.listdir(Config.TEMP_DIR):
                            if item.startswith('voice_samples_') and os.path.isdir(os.path.join(Config.TEMP_DIR, item)):
                                session_id = item.replace('voice_samples_', '')
                                session_path = os.path.join(Config.TEMP_DIR, item)
                                
                                # 세션 정보 수집
                                sample_count = len([f for f in os.listdir(session_path) if f.endswith('.wav')])
                                folder_size = sum(os.path.getsize(os.path.join(session_path, f)) 
                                                for f in os.listdir(session_path) if os.path.isfile(os.path.join(session_path, f)))
                                
                                all_sessions.append({
                                    'id': session_id,
                                    'path': session_path,
                                    'samples': sample_count,
                                    'size': folder_size / 1024  # KB
                                })
                    
                    if all_sessions:
                        st.info(f"📊 총 **{len(all_sessions)}개**의 음성 세션을 발견했습니다")
                        
                        for session in all_sessions:
                            is_active = hasattr(st.session_state, 'voice_session_id') and st.session_state.voice_session_id == session['id']
                            status_icon = "🟢" if is_active else "⚪"
                            
                            col1, col2, col3 = st.columns([2, 1, 1])
                            
                            with col1:
                                st.write(f"{status_icon} **{session['id']}** ({session['samples']}개 샘플, {session['size']:.1f}KB)")
                            
                            with col2:
                                if not is_active and st.button("🔄 활성화", key=f"activate_{session['id']}", use_container_width=True):
                                    st.session_state.voice_session_id = session['id']
                                    st.session_state.voice_samples_dir = session['path']
                                    st.success(f"✅ 세션 {session['id']} 활성화!")
                                    st.rerun()
                            
                            with col3:
                                if st.button("🗑️ 삭제", key=f"delete_{session['id']}", use_container_width=True):
                                    try:
                                        import shutil
                                        shutil.rmtree(session['path'])
                                        st.success(f"✅ 세션 {session['id']} 삭제 완료!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"삭제 실패: {e}")
                        
                        # 전체 정리 버튼
                        if st.button("🧹 모든 세션 정리", key="cleanup_all_sessions", type="secondary"):
                            deleted_count = 0
                            for session in all_sessions:
                                try:
                                    import shutil
                                    shutil.rmtree(session['path'])
                                    deleted_count += 1
                                except:
                                    pass
                            
                            # 활성 세션도 정리
                            if hasattr(st.session_state, 'voice_session_id'):
                                delattr(st.session_state, 'voice_session_id')
                            if hasattr(st.session_state, 'voice_samples_dir'):
                                delattr(st.session_state, 'voice_samples_dir')
                            
                            st.success(f"🧹 {deleted_count}개 세션이 정리되었습니다!")
                            st.rerun()
                    else:
                        st.write("저장된 음성 세션이 없습니다.")
        
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
    
    # Additional sections (outside tabs)
    st.markdown("---")
    show_additional_features()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>🎬 AutoAvatar - AI 뉴스 비디오 생성기</p>
        <p>❤️ Streamlit, OpenAI, MoviePy로 제작</p>
    </div>
    """, unsafe_allow_html=True)

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