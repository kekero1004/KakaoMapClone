#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
간단한 실행 스크립트 - 에러가 적은 기본 버전
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        # WebEngine을 위한 속성 설정 (애플리케이션 생성 전에 호출)
        from PyQt6.QtCore import Qt
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
        
        # PyQt6 애플리케이션 생성
        app = QApplication(sys.argv)
        app.setApplicationName("KakaoMap Clone Simple")
        
        # 설정 로드
        from utils.config import Config
        config = Config()
        
        # 메인 윈도우 생성
        from ui.main_window import MainWindow
        window = MainWindow(config)
        
        # 윈도우 표시
        window.show()
        
        # 애플리케이션 실행
        return app.exec()
        
    except ImportError as e:
        print(f"모듈 import 오류: {e}")
        print("다음 명령으로 필요한 패키지를 설치하세요:")
        print("pip install PyQt6 PyQt6-WebEngine requests Pillow")
        return 1
        
    except Exception as e:
        print(f"애플리케이션 실행 오류: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)