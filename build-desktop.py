#!/usr/bin/env python3
"""
AutoAvatar Desktop Build Script
Electron 앱을 빌드하기 위한 스크립트
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, cwd=None):
    """명령어 실행"""
    print(f"🔄 실행 중: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, cwd=cwd)
        print(f"✅ 성공: {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 실패: {command} (코드: {e.returncode})")
        return False

def check_node_npm():
    """Node.js와 npm 설치 확인"""
    print("🔍 Node.js 및 npm 확인 중...")
    
    if not run_command("node --version"):
        print("❌ Node.js가 설치되지 않았습니다!")
        print("   https://nodejs.org에서 Node.js를 설치해주세요.")
        return False
    
    if not run_command("npm --version"):
        print("❌ npm이 설치되지 않았습니다!")
        return False
    
    return True

def install_dependencies():
    """의존성 설치"""
    print("📦 npm 의존성 설치 중...")
    return run_command("npm install")

def create_icon_placeholder():
    """아이콘 플레이스홀더 생성"""
    print("🎨 아이콘 파일 확인 중...")
    
    icon_dir = Path("electron/assets")
    icon_files = [
        "icon.png",
        "icon.ico", 
        "icon.icns"
    ]
    
    for icon_file in icon_files:
        icon_path = icon_dir / icon_file
        if not icon_path.exists():
            print(f"⚠️  {icon_file} 파일이 없습니다. 기본 아이콘을 사용합니다.")

def build_app():
    """앱 빌드"""
    print("🏗️  AutoAvatar 데스크톱 앱 빌드 시작...")
    
    # Windows용 빌드
    if sys.platform.startswith('win'):
        print("🪟 Windows 버전 빌드 중...")
        return run_command("npm run build-win")
    
    # macOS용 빌드
    elif sys.platform == 'darwin':
        print("🍎 macOS 버전 빌드 중...")
        return run_command("npm run build-mac")
    
    # Linux용 빌드
    else:
        print("🐧 Linux 버전 빌드 중...")
        return run_command("npm run build-linux")

def main():
    """메인 함수"""
    print("🚀 AutoAvatar Desktop 빌드 스크립트")
    print("=" * 50)
    
    # 현재 디렉토리 확인
    if not Path("app.py").exists():
        print("❌ app.py 파일을 찾을 수 없습니다!")
        print("   AutoAvatar 프로젝트 루트 디렉토리에서 실행해주세요.")
        sys.exit(1)
    
    # Node.js 환경 확인
    if not check_node_npm():
        sys.exit(1)
    
    # 의존성 설치
    if not install_dependencies():
        print("❌ npm 의존성 설치에 실패했습니다!")
        sys.exit(1)
    
    # 아이콘 확인
    create_icon_placeholder()
    
    # 앱 빌드
    if build_app():
        print("🎉 빌드 완료!")
        print("📁 빌드된 파일은 'dist' 폴더에 있습니다.")
        
        # 빌드 결과 표시
        dist_dir = Path("dist")
        if dist_dir.exists():
            print("\n📦 빌드된 파일들:")
            for item in dist_dir.iterdir():
                if item.is_file():
                    size = item.stat().st_size / 1024 / 1024  # MB
                    print(f"   📄 {item.name} ({size:.1f} MB)")
                elif item.is_dir():
                    print(f"   📁 {item.name}/")
    else:
        print("❌ 빌드에 실패했습니다!")
        sys.exit(1)

if __name__ == "__main__":
    main() 