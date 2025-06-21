import streamlit as st
from typing import Dict, Any
from .config_manager import config_manager

def render_api_key_setup() -> bool:
    """API 키 설정 UI 렌더링"""
    
    st.markdown("## 🔑 API 키 설정")
    st.markdown("---")
    
    # 서비스 정보 가져오기
    services = config_manager.get_service_info()
    validation_results = config_manager.validate_api_keys()
    
    # 전체 상태 표시
    all_required_set = validation_results.get('openai', False)
    any_voice_set = validation_results.get('elevenlabs', False) or validation_results.get('azure', False)
    
    if all_required_set and any_voice_set:
        st.success("✅ 모든 필수 API 키가 설정되었습니다!")
    elif all_required_set:
        st.warning("⚠️ OpenAI API 키는 설정되었지만, 음성 합성 API 키를 추가하면 더 좋은 품질의 음성을 사용할 수 있습니다.")
    else:
        st.error("❌ OpenAI API 키가 필요합니다.")
    
    # 각 서비스별 설정 섹션
    for service_key, service_info in services.items():
        render_service_section(service_key, service_info, validation_results)
    
    # 추가 옵션
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 키 검증", help="입력된 API 키들의 유효성을 검증합니다"):
            validate_all_keys()
    
    with col2:
        if st.button("🗑️ 모든 키 삭제", help="저장된 모든 API 키를 삭제합니다"):
            config_manager.clear_all_keys()
            st.rerun()
    
    with col3:
        if st.button("📤 설정 내보내기", help="현재 설정을 .env 파일 형태로 내보냅니다"):
            export_config()
    
    return all_required_set

def render_service_section(service_key: str, service_info: Dict[str, Any], validation_results: Dict[str, bool]):
    """개별 서비스 설정 섹션 렌더링"""
    
    is_valid = validation_results.get(service_key, False)
    current_key = config_manager.get_api_key(service_key)
    
    # 섹션 헤더
    status_icon = "✅" if is_valid else ("❌" if service_info['required'] else "⚪")
    required_text = " (필수)" if service_info['required'] else " (선택)"
    
    with st.expander(f"{status_icon} {service_info['name']}{required_text}", expanded=not is_valid):
        
        # 서비스 설명
        st.markdown(f"**설명:** {service_info['description']}")
        st.markdown(f"**가격:** {service_info['pricing']}")
        st.markdown(f"**키 형식:** `{service_info['key_format']}`")
        
        # 링크 버튼들
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"[🚀 회원가입]({service_info['signup_url']})")
        with col2:
            st.markdown(f"[🔑 API 키 발급]({service_info['api_url']})")
        
        # API 키 입력
        key_placeholder = f"여기에 {service_info['name']} API 키를 입력하세요..."
        
        # 현재 키가 있으면 마스킹해서 표시
        if current_key:
            display_key = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else current_key
            key_placeholder = f"현재 설정됨: {display_key}"
        
        new_key = st.text_input(
            f"{service_info['name']} API 키",
            value="",
            placeholder=key_placeholder,
            type="password",
            key=f"input_{service_key}",
            help=f"{service_info['name']} API 키를 입력하세요"
        )
        
        # 저장 옵션
        col1, col2 = st.columns(2)
        with col1:
            save_to_file = st.checkbox(
                "로컬에 저장", 
                value=True, 
                key=f"save_{service_key}",
                help="체크하면 다음에 앱을 실행할 때도 키가 유지됩니다"
            )
        
        with col2:
            if st.button(f"💾 저장", key=f"save_btn_{service_key}"):
                if new_key.strip():
                    config_manager.set_api_key(service_key, new_key.strip(), save_to_file)
                    st.success(f"{service_info['name']} API 키가 저장되었습니다!")
                    st.rerun()
                else:
                    st.error("API 키를 입력해주세요.")
        
        # 현재 상태 표시
        if current_key:
            if is_valid:
                st.success("✅ 유효한 API 키가 설정되어 있습니다.")
            else:
                st.warning("⚠️ API 키가 설정되어 있지만 형식이 올바르지 않을 수 있습니다.")
        else:
            if service_info['required']:
                st.error("❌ 필수 API 키가 설정되지 않았습니다.")
            else:
                st.info("ℹ️ 선택적 API 키입니다. 설정하면 더 좋은 품질을 제공합니다.")

def validate_all_keys():
    """모든 API 키 유효성 검증"""
    validation_results = config_manager.validate_api_keys()
    
    st.markdown("### 🔍 API 키 검증 결과")
    
    for service, is_valid in validation_results.items():
        service_info = config_manager.get_service_info()[service]
        if is_valid:
            st.success(f"✅ {service_info['name']}: 유효")
        else:
            current_key = config_manager.get_api_key(service)
            if current_key:
                st.error(f"❌ {service_info['name']}: 형식이 올바르지 않음")
            else:
                status = "필수" if service_info['required'] else "선택"
                st.warning(f"⚪ {service_info['name']}: 설정되지 않음 ({status})")

def export_config():
    """설정 내보내기"""
    config_text = config_manager.export_config()
    
    if config_text:
        st.markdown("### 📤 설정 내보내기")
        st.markdown("아래 내용을 `.env` 파일로 저장하세요:")
        st.code(config_text, language="bash")
        
        # 다운로드 버튼
        st.download_button(
            label="📥 .env 파일 다운로드",
            data=config_text,
            file_name=".env",
            mime="text/plain"
        )
    else:
        st.warning("내보낼 설정이 없습니다.")

def show_api_key_status():
    """간단한 API 키 상태 표시 (사이드바용)"""
    validation_results = config_manager.validate_api_keys()
    
    openai_status = "✅" if validation_results.get('openai', False) else "❌"
    elevenlabs_status = "✅" if validation_results.get('elevenlabs', False) else "⚪"
    azure_status = "✅" if validation_results.get('azure', False) else "⚪"
    
    st.markdown(f"""
    **API 키 상태:**
    - OpenAI: {openai_status}
    - ElevenLabs: {elevenlabs_status}
    - Azure: {azure_status}
    """)
    
    return validation_results.get('openai', False) 