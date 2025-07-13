from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QSlider, QGroupBox, QGridLayout)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import pyqtSignal, Qt, QThread, pyqtSlot, QTimer, QUrl
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import requests
from typing import Optional


class RoadviewWidget(QWidget):
    roadview_moved = pyqtSignal(float, float, float)  # lat, lng, angle
    roadview_closed = pyqtSignal()
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.current_x = 126.9780
        self.current_y = 37.5665
        self.current_pan = 0
        self.current_tilt = 0
        self.current_level = 1
        self.image_size = (640, 360)
        self.is_visible = False
        self.roadview_timer = None
        self.last_roadview_timestamp = 0
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        # 헤더
        header_layout = QHBoxLayout()
        title_label = QLabel("로드뷰")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setMaximumSize(30, 30)
        self.close_btn.clicked.connect(self.close_roadview)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.close_btn)
        
        layout.addLayout(header_layout)
        
        # 현재 위치 표시
        self.location_label = QLabel("위치: 로드뷰를 로드하세요")
        self.location_label.setStyleSheet("color: #666666; font-size: 10px;")
        layout.addWidget(self.location_label)
        
        # 이미지 표시 영역
        self.setup_image_display(layout)
        
        # 컨트롤 패널
        self.setup_controls(layout)
        
        self.setLayout(layout)
        self.setMinimumHeight(400)
        self.hide()  # 초기에는 숨김
    
    def setup_image_display(self, layout):
        """웹 로드뷰 표시 영역 설정"""
        self.web_view = QWebEngineView()
        self.web_view.setMinimumHeight(300)
        
        # 웹 엔진 설정
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        
        layout.addWidget(self.web_view)
    
    def setup_controls(self, layout):
        """컨트롤 버튼 설정"""
        controls_group = QGroupBox("로드뷰 컨트롤")
        controls_layout = QGridLayout()
        
        
        
        
        # 새로고침 버튼
        self.refresh_btn = QPushButton("새로고침")
        self.refresh_btn.clicked.connect(self.refresh_roadview)
        controls_layout.addWidget(self.refresh_btn, 0, 0)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
    
    def load_roadview(self, x: float, y: float):
        """로드뷰 로드"""
        self.current_x = x
        self.current_y = y
        self.current_pan = 0
        self.current_tilt = 0
        self.current_level = 1
        
        
        self.update_location_label()
        self.update_image()
        
        # MapWalker 위치 업데이트
        self.roadview_moved.emit(self.current_y, self.current_x, float(self.current_pan))
        
        if not self.is_visible:
            self.show()
            self.is_visible = True
    
    def update_location_label(self):
        """위치 라벨 업데이트"""
        self.location_label.setText(f"위치: {self.current_y:.6f}, {self.current_x:.6f}")
    
    def update_image(self):
        """웹 로드뷰 업데이트"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Kakao Roadview</title>
            <style>
                body, html {{ margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; }}
                #roadview {{ width: 100%; height: 100%; }}
                #loading {{ 
                    position: absolute; 
                    top: 50%; 
                    left: 50%; 
                    transform: translate(-50%, -50%);
                    font-size: 16px;
                    z-index: 1000;
                }}
            </style>
        </head>
        <body>
            <div id="loading">🛣️ 로드뷰 로딩 중...</div>
            <div id="roadview"></div>
            
            <script type="text/javascript" src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={self.api_key}&autoload=false"></script>
            <script>
                console.log("카카오맵 로드뷰 SDK 로딩 시작");
                
                kakao.maps.load(function() {{
                    console.log("카카오맵 SDK 로드 완료");
                    
                    // 로딩 메시지 숨기기
                    document.getElementById('loading').style.display = 'none';
                    
                    var container = document.getElementById('roadview');
                    var roadview = new kakao.maps.Roadview(container);
                    var roadviewClient = new kakao.maps.RoadviewClient();
                    
                    var position = new kakao.maps.LatLng({self.current_y}, {self.current_x});
                    
                    // 로드뷰 생성
                    roadviewClient.getNearestPanoId(position, 50, function(panoId) {{
                        if (panoId === null) {{
                            document.getElementById('roadview').innerHTML = '<div style="text-align:center; padding-top:100px;">로드뷰를 사용할 수 없는 위치입니다</div>';
                        }} else {{
                            roadview.setPanoId(panoId, position);
                            roadview.setViewpoint({{
                                pan: {self.current_pan},
                                tilt: {self.current_tilt},
                                zoom: {self.current_level}
                            }});
                            
                            // 로드뷰 이벤트 리스너
                            kakao.maps.event.addListener(roadview, 'viewpoint_changed', function() {{
                                var viewpoint = roadview.getViewpoint();
                                var position = roadview.getPosition();
                                
                                if (typeof window.roadviewMoved === 'function') {{
                                    window.roadviewMoved(
                                        position.getLat(), 
                                        position.getLng(), 
                                        viewpoint.pan
                                    );
                                }}
                            }});
                            
                            console.log("로드뷰 초기화 완료");
                        }}
                    }});
                    
                    // Python에서 호출할 함수들
                    window.updateViewpoint = function(pan, tilt, zoom) {{
                        roadview.setViewpoint({{
                            pan: pan,
                            tilt: tilt,
                            zoom: zoom
                        }});
                    }};
                    
                    window.moveRoadview = function(lat, lng) {{
                        var newPosition = new kakao.maps.LatLng(lat, lng);
                        roadviewClient.getNearestPanoId(newPosition, 50, function(panoId) {{
                            if (panoId !== null) {{
                                roadview.setPanoId(panoId, newPosition);
                            }}
                        }});
                    }};
                }});
                
                // 로드뷰 이동 콜백 설정
                window.roadviewMoved = function(lat, lng, pan) {{
                    console.log('Roadview moved:', lat, lng, pan);
                }};
                
                // 스크립트 로드 오류 처리
                window.addEventListener('error', function(e) {{
                    console.error("스크립트 오류:", e);
                    document.getElementById('loading').innerHTML = "❌ 카카오맵 API 로드 실패<br>API 키를 확인해주세요";
                }});
            </script>
        </body>
        </html>
        """
        
        self.web_view.setHtml(html_content)
        
        # JavaScript 콜백 설정
        QTimer.singleShot(1000, self.setup_roadview_callbacks)
    
    def setup_roadview_callbacks(self):
        """로드뷰 JavaScript 콜백 설정"""
        script = """
            window.roadviewMoved = function(lat, lng, pan) {
                console.log('Roadview moved:', lat, lng, pan);
                window.lastRoadviewMove = {lat: lat, lng: lng, pan: pan, timestamp: Date.now()};
            };
        """
        self.web_view.page().runJavaScript(script)
        
        # 주기적으로 로드뷰 이동 확인
        self.roadview_timer = QTimer()
        self.roadview_timer.timeout.connect(self.check_roadview_callbacks)
        self.roadview_timer.start(100)
        self.last_roadview_timestamp = 0
    
    def check_roadview_callbacks(self):
        """로드뷰 콜백 확인"""
        script = """
        (function() {
            if (window.lastRoadviewMove) {
                var result = JSON.stringify(window.lastRoadviewMove);
                window.lastRoadviewMove = null;
                return result;
            }
            return null;
        })();
        """
        self.web_view.page().runJavaScript(script, self._handle_roadview_callback)
    
    def _handle_roadview_callback(self, result_str):
        """로드뷰 콜백 결과 처리"""
        try:
            import json
            if result_str:
                result = json.loads(result_str)
                timestamp = result.get('timestamp', 0)
                if timestamp > self.last_roadview_timestamp:
                    self.last_roadview_timestamp = timestamp
                    self.current_x = result['lng']
                    self.current_y = result['lat']
                    self.current_pan = result['pan']
                    self.update_location_label()
                    self.roadview_moved.emit(result['lat'], result['lng'], result['pan'])
        except Exception as e:
            print(f"로드뷰 콜백 처리 오류: {e}")
    
    
    def update_viewpoint(self):
        """로드뷰 시점 업데이트"""
        script = f"updateViewpoint({self.current_pan}, {self.current_tilt}, {self.current_level});"
        self.web_view.page().runJavaScript(script)
    
    def refresh_roadview(self):
        """로드뷰 새로고침"""
        self.update_image()
    
    def close_roadview(self):
        """로드뷰 닫기"""
        if self.roadview_timer:
            self.roadview_timer.stop()
        self.hide()
        self.is_visible = False
        self.roadview_closed.emit()
    
    def resizeEvent(self, event):
        """위젯 크기 변경 시 웹뷰 크기 조정"""
        super().resizeEvent(event)
        # 웹뷰가 사용할 수 있는 높이 계산 (헤더, 위치 라벨, 컨트롤 제외)
        if hasattr(self, 'web_view'):
            available_height = self.height() - 100  # 헤더와 작은 컨트롤 영역 고려
            if available_height > 200:  # 최소 높이 보장
                self.web_view.setMinimumHeight(available_height)
    
    def closeEvent(self, event):
        """위젯 종료 시 타이머 정리"""
        if self.roadview_timer:
            self.roadview_timer.stop()
        super().closeEvent(event)