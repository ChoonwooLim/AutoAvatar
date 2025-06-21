#!/usr/bin/env python3
"""
로컬 네트워크에서 AutoAvatar 공유 설정
같은 Wi-Fi 네트워크의 다른 기기들이 접근할 수 있도록 설정
"""

import socket
import subprocess
import sys
import platform

def get_local_ip():
    """현재 컴퓨터의 로컬 IP 주소 가져오기"""
    try:
        # 임시 소켓을 생성하여 로컬 IP 확인
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def check_firewall_settings():
    """방화벽 설정 체크 및 안내"""
    os_type = platform.system()
    
    print("🔥 방화벽 설정 안내:")
    
    if os_type == "Windows":
        print("Windows 방화벽 설정:")
        print("1. Windows 설정 > 업데이트 및 보안 > Windows 보안")
        print("2. 방화벽 및 네트워크 보호")
        print("3. '앱에서 방화벽 통과 허용'")
        print("4. Python.exe 찾아서 '개인' 및 '공용' 체크")
        
    elif os_type == "Darwin":  # macOS
        print("macOS 방화벽 설정:")
        print("1. 시스템 환경설정 > 보안 및 개인 정보 보호")
        print("2. 방화벽 탭")
        print("3. 방화벽 옵션... > Python 허용")
        
    else:  # Linux
        print("Linux 방화벽 설정:")
        print("sudo ufw allow 8501")

def generate_network_urls(port=8501):
    """네트워크 접근 URL들 생성"""
    local_ip = get_local_ip()
    
    urls = {
        "로컬": f"http://localhost:{port}",
        "네트워크": f"http://{local_ip}:{port}",
        "QR코드용": f"http://{local_ip}:{port}"
    }
    
    return urls, local_ip

def create_qr_code(url):
    """QR 코드 생성 (선택사항)"""
    try:
        import qrcode
        from PIL import Image
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_path = "autoavatar_qr.png"
        qr_img.save(qr_path)
        
        return qr_path
    except ImportError:
        return None

def main():
    """메인 실행 함수"""
    print("🌐 AutoAvatar 네트워크 공유 설정")
    print("=" * 50)
    
    # IP 및 URL 정보 생성
    urls, local_ip = generate_network_urls()
    
    print(f"🖥️  현재 컴퓨터 IP: {local_ip}")
    print(f"🔗 접근 URL들:")
    for name, url in urls.items():
        print(f"   {name}: {url}")
    
    print("\n📱 모바일/다른 PC에서 접근 방법:")
    print(f"   1. 같은 Wi-Fi 네트워크에 연결")
    print(f"   2. 브라우저에서 {urls['네트워크']} 접속")
    
    # QR 코드 생성
    qr_path = create_qr_code(urls['QR코드용'])
    if qr_path:
        print(f"\n📱 QR 코드 생성됨: {qr_path}")
        print("   모바일에서 QR 코드 스캔하여 바로 접속 가능!")
    
    # 방화벽 설정 안내
    print("\n" + "=" * 50)
    check_firewall_settings()
    
    print("\n🚀 실행 명령어:")
    print("streamlit run app.py --server.address 0.0.0.0 --server.port 8501")
    
    print("\n💡 팁:")
    print("- 방화벽에서 8501 포트 허용 필요")
    print("- 같은 Wi-Fi 네트워크의 모든 기기에서 접근 가능")
    print("- 보안을 위해 외부 인터넷에는 노출되지 않음")

if __name__ == "__main__":
    main() 