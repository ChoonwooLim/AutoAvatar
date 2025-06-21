#!/usr/bin/env python3
"""
ngrok을 사용한 AutoAvatar 즉시 공개 링크 생성
전 세계 어디서나 접근 가능한 임시 URL 생성
"""

import subprocess
import sys
import time
import requests
import json
import os

def install_ngrok():
    """ngrok 설치 안내"""
    print("🚀 ngrok 설치 방법:")
    print("1. https://ngrok.com/ 에서 계정 생성 (무료)")
    print("2. 다운로드 및 설치:")
    print("   Windows: https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip")
    print("   Mac: brew install ngrok")
    print("   Linux: https://ngrok.com/download")
    print("3. 인증 토큰 설정: ngrok config add-authtoken YOUR_TOKEN")

def check_ngrok_installed():
    """ngrok 설치 여부 확인"""
    try:
        result = subprocess.run(['ngrok', 'version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ ngrok 설치됨: {result.stdout.strip()}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("❌ ngrok이 설치되지 않음")
    return False

def get_ngrok_tunnels():
    """활성 ngrok 터널 정보 가져오기"""
    try:
        response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
        if response.status_code == 200:
            tunnels = response.json()['tunnels']
            return tunnels
        return []
    except:
        return []

def create_public_link():
    """공개 링크 생성 및 관리"""
    print("🌍 AutoAvatar 공개 링크 생성 중...")
    
    # ngrok 설치 확인
    if not check_ngrok_installed():
        install_ngrok()
        return False
    
    # Streamlit 실행 확인 메시지
    print("\n📋 실행 순서:")
    print("1. 터미널 1: streamlit run app.py")
    print("2. 터미널 2: 이 스크립트 실행")
    print("3. 생성된 공개 URL로 전 세계 접근 가능")
    
    # ngrok 터널 생성 명령어 안내
    print("\n🚀 ngrok 실행 명령어:")
    print("ngrok http 8501")
    
    # ngrok 실행 (백그라운드)
    try:
        print("\n🔗 ngrok 터널 생성 중...")
        ngrok_process = subprocess.Popen(
            ['ngrok', 'http', '8501'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 잠시 대기 후 터널 정보 확인
        time.sleep(3)
        
        tunnels = get_ngrok_tunnels()
        if tunnels:
            for tunnel in tunnels:
                if tunnel['config']['addr'] == 'http://localhost:8501':
                    public_url = tunnel['public_url']
                    print(f"🎉 공개 링크 생성 완료!")
                    print(f"🔗 URL: {public_url}")
                    print(f"📱 이 링크를 전 세계 어디서나 접근 가능!")
                    
                    # QR 코드 생성
                    create_qr_for_url(public_url)
                    
                    return public_url
        
        print("⏳ ngrok 터널 생성 중... 잠시만 기다려주세요")
        return None
        
    except Exception as e:
        print(f"❌ ngrok 실행 오류: {e}")
        return None

def create_qr_for_url(url):
    """URL용 QR 코드 생성"""
    try:
        import qrcode
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_path = "autoavatar_public_qr.png"
        qr_img.save(qr_path)
        
        print(f"📱 QR 코드 생성됨: {qr_path}")
        print("   모바일에서 QR 코드 스캔하여 바로 접속!")
        
    except ImportError:
        print("💡 QR 코드 생성을 위해 'pip install qrcode[pil]' 설치 권장")

def create_sharing_guide():
    """공유 가이드 생성"""
    guide = """
# 🎬 AutoAvatar 체험 링크

## 🌐 접속 방법
1. 아래 링크 클릭
2. 사진 업로드 (JPG, PNG)
3. 뉴스 주제 입력
4. "Generate Video" 클릭
5. 완성된 비디오 다운로드

## 🎭 음성 복제 기능
- 사이드바의 "Voice Cloning" 탭
- 비디오/오디오 파일에서 음성 추출
- 마이크로폰으로 직접 녹음
- 복제된 음성으로 비디오 생성

## ⚠️ 주의사항
- 임시 링크로 세션 종료 시 사라짐
- API 키 필요 (OpenAI, ElevenLabs 등)
- 개인정보 업로드 시 주의

## 🛠️ 기술 스택
- Python + Streamlit
- OpenAI GPT-4 (스크립트 생성)
- ElevenLabs/Azure (음성 합성)
- MoviePy (비디오 편집)
- 음성 복제 시스템

Made with ❤️ using AI
"""
    
    with open("sharing_guide.md", "w", encoding="utf-8") as f:
        f.write(guide)
    
    print("📖 공유 가이드 생성됨: sharing_guide.md")

def main():
    """메인 실행 함수"""
    print("🌍 AutoAvatar 공개 링크 생성기")
    print("=" * 50)
    
    # 공개 링크 생성
    public_url = create_public_link()
    
    if public_url:
        # 공유 가이드 생성
        create_sharing_guide()
        
        print("\n" + "=" * 50)
        print("🎉 AutoAvatar 공개 링크 준비 완료!")
        print(f"🔗 공유용 URL: {public_url}")
        print("📧 이메일, 카카오톡, SNS로 링크 공유 가능")
        print("🌍 전 세계 어디서나 접속 가능")
        print("⏰ ngrok 프로세스 종료 시까지 유효")
        
        print("\n💡 사용 팁:")
        print("- Streamlit 앱이 실행 중이어야 함")
        print("- ngrok 프로세스를 종료하지 마세요")
        print("- 무료 버전은 세션당 2시간 제한")
        
    else:
        print("\n❌ 공개 링크 생성 실패")
        print("🔧 해결 방법:")
        print("1. ngrok 설치 및 인증")
        print("2. Streamlit 앱 실행 확인")
        print("3. 방화벽 설정 확인")

if __name__ == "__main__":
    main() 