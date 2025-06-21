#!/usr/bin/env python3
"""
AutoAvatar Desktop 개발 실행 스크립트
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_command(command, cwd=None, background=False):
    """명령어 실행"""
    print(f"🔄 실행 중: {command}")
    try:
        if background:
            return subprocess.Popen(command, shell=True, cwd=cwd)
        else:
            result = subprocess.run(command, shell=True, check=True, cwd=cwd)
            return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 실패: {command} (코드: {e.returncode})")
        return False

def check_dependencies():
    """의존성 확인"""
    print("🔍 의존성 확인 중...")
    
    # Node.js 확인
    if not run_command("node --version"):
        print("❌ Node.js가 설치되지 않았습니다!")
        return False
    
    # npm 확인
    if not run_command("npm --version"):
        print("❌ npm이 설치되지 않았습니다!")
        return False
    
    # Python 패키지 확인
    try:
        import streamlit
        print("✅ Streamlit 설치됨")
    except ImportError:
        print("❌ Streamlit이 설치되지 않았습니다!")
        print("   pip install streamlit 명령어로 설치해주세요.")
        return False
    
    return True

def install_npm_dependencies():
    """npm 의존성 설치"""
    if not Path("node_modules").exists():
        print("📦 npm 의존성 설치 중...")
        return run_command("npm install")
    else:
        print("✅ npm 의존성이 이미 설치되어 있습니다.")
        return True

def main():
    """메인 함수"""
    print("🚀 AutoAvatar Desktop 개발 모드")
    print("=" * 40)
    
    # 현재 디렉토리 확인
    if not Path("app.py").exists():
        print("❌ app.py 파일을 찾을 수 없습니다!")
        print("   AutoAvatar 프로젝트 루트 디렉토리에서 실행해주세요.")
        sys.exit(1)
    
    # 의존성 확인
    if not check_dependencies():
        sys.exit(1)
    
    # npm 의존성 설치
    if not install_npm_dependencies():
        print("❌ npm 의존성 설치에 실패했습니다!")
        sys.exit(1)
    
    print("🎯 개발 모드로 AutoAvatar Desktop 실행 중...")
    print("   - Streamlit 서버가 자동으로 시작됩니다")
    print("   - Electron 창이 열립니다")
    print("   - 종료하려면 Ctrl+C를 누르세요")
    print()
    
    # 개발 모드 실행
    try:
        run_command("npm run dev")
    except KeyboardInterrupt:
        print("\n🛑 종료 중...")
        print("✅ AutoAvatar Desktop이 종료되었습니다.")

if __name__ == "__main__":
    main() 