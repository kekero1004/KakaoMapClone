#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
지도 테스트 스크립트 - 지도가 제대로 로드되는지 확인
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        # WebEngine을 위한 속성 설정
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
        
        # 애플리케이션 생성
        app = QApplication(sys.argv)
        app.setApplicationName("KakaoMap Test")
        
        # 설정 로드
        from utils.config import Config
        config = Config()
        
        # API 키 확인
        js_api_key = config.get_api_key('kakao_javascript_api_key')
        print(f"JavaScript API 키: {js_api_key[:10]}..." if js_api_key else "API 키 없음")
        
        # 메인 윈도우 생성
        window = QMainWindow()
        window.setWindowTitle("카카오맵 테스트")
        window.resize(800, 600)
        
        # 중앙 위젯
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        # 지도 위젯 생성
        from ui.map_widget import MapWidget
        map_widget = MapWidget(js_api_key)
        layout.addWidget(map_widget)
        
        central_widget.setLayout(layout)
        window.setCentralWidget(central_widget)
        
        # 윈도우 표시
        window.show()
        
        print("지도 테스트 창이 열렸습니다.")
        print("지도가 제대로 표시되는지 확인해주세요.")
        
        # 애플리케이션 실행
        return app.exec()
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)