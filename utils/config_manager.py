import os
import json
import streamlit as st
from typing import Dict, Optional
from pathlib import Path

class ConfigManager:
    """동적 API 키 및 설정 관리 클래스"""
    
    def __init__(self):
        self.config_file = Path("user_config.json")
        self.session_config = {}
        self.load_config()
    
    def load_config(self):
        """저장된 설정 로드"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.session_config = json.load(f)
        except Exception as e:
            print(f"설정 로드 오류: {e}")
            self.session_config = {}
    
    def save_config(self):
        """설정 저장"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"설정 저장 오류: {e}")
    
    def get_api_key(self, service: str) -> Optional[str]:
        """API 키 가져오기 (세션 > 파일 > 환경변수 순)"""
        # 1. 세션에서 확인
        session_key = f"{service.upper()}_API_KEY"
        if session_key in st.session_state:
            return st.session_state[session_key]
        
        # 2. 저장된 설정에서 확인
        if session_key in self.session_config:
            return self.session_config[session_key]
        
        # 3. 환경변수에서 확인
        return os.getenv(session_key)
    
    def set_api_key(self, service: str, api_key: str, save_to_file: bool = True):
        """API 키 설정"""
        session_key = f"{service.upper()}_API_KEY"
        
        # 세션에 저장
        st.session_state[session_key] = api_key
        
        # 파일에 저장 (선택적)
        if save_to_file and api_key.strip():
            self.session_config[session_key] = api_key
            self.save_config()
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """API 키 유효성 검증"""
        validation_results = {}
        
        # OpenAI 키 검증
        openai_key = self.get_api_key('openai')
        validation_results['openai'] = bool(openai_key and openai_key.startswith('sk-'))
        
        # ElevenLabs 키 검증
        elevenlabs_key = self.get_api_key('elevenlabs')
        validation_results['elevenlabs'] = bool(elevenlabs_key and len(elevenlabs_key) > 10)
        
        # Azure 키 검증
        azure_key = self.get_api_key('azure_speech')
        validation_results['azure'] = bool(azure_key and len(azure_key) > 10)
        
        return validation_results
    
    def get_service_info(self) -> Dict[str, Dict]:
        """각 서비스 정보 반환"""
        return {
            'openai': {
                'name': 'OpenAI GPT-4',
                'description': 'AI 뉴스 스크립트 생성 (필수)',
                'signup_url': 'https://platform.openai.com/signup',
                'api_url': 'https://platform.openai.com/api-keys',
                'pricing': '사용량 기반 ($0.03/1K tokens)',
                'required': True,
                'key_format': 'sk-...'
            },
            'elevenlabs': {
                'name': 'ElevenLabs',
                'description': '프리미엄 AI 음성 합성 (권장)',
                'signup_url': 'https://elevenlabs.io/sign-up',
                'api_url': 'https://elevenlabs.io/app/speech-synthesis',
                'pricing': '무료: 월 10,000자 / 유료: $5/월부터',
                'required': False,
                'key_format': '32자리 문자열'
            },
            'azure': {
                'name': 'Azure Speech Services',
                'description': 'Microsoft 음성 합성 (대안)',
                'signup_url': 'https://azure.microsoft.com/free/',
                'api_url': 'https://portal.azure.com',
                'pricing': '무료: 월 500,000자 / 유료: $1/1M자',
                'required': False,
                'key_format': '32자리 문자열'
            }
        }
    
    def clear_all_keys(self):
        """모든 API 키 삭제"""
        services = ['openai', 'elevenlabs', 'azure_speech']
        
        for service in services:
            session_key = f"{service.upper()}_API_KEY"
            if session_key in st.session_state:
                del st.session_state[session_key]
            if session_key in self.session_config:
                del self.session_config[session_key]
        
        self.save_config()
    
    def export_config(self) -> str:
        """설정을 환경변수 형태로 내보내기"""
        lines = []
        for key, value in self.session_config.items():
            if value:
                lines.append(f"{key}={value}")
        return "\n".join(lines)

# 전역 설정 관리자 인스턴스
config_manager = ConfigManager() 