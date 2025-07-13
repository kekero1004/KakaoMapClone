from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTextEdit, QGroupBox, 
                             QTabWidget, QWidget, QFormLayout, QSpinBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont
from api.kakao_map_api import KakaoMapAPI
import json


class GeocodingWorker(QThread):
    """지오코딩 작업을 처리하는 워커 스레드"""
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api: KakaoMapAPI, task_type: str, **kwargs):
        super().__init__()
        self.api = api
        self.task_type = task_type
        self.kwargs = kwargs
    
    def run(self):
        try:
            if self.task_type == "address_to_coord":
                result = self.api.search_address(self.kwargs['address'])
            elif self.task_type == "coord_to_address":
                result = self.api.coord_to_address(self.kwargs['x'], self.kwargs['y'])
            
            if result:
                self.result_ready.emit(result)
            else:
                self.error_occurred.emit("검색 결과가 없습니다.")
        except Exception as e:
            self.error_occurred.emit(f"오류가 발생했습니다: {str(e)}")


class GeocodingDialog(QDialog):
    """지오코딩 및 역지오코딩 다이얼로그"""
    location_selected = pyqtSignal(float, float, str)  # lat, lng, description
    
    def __init__(self, api: KakaoMapAPI, parent=None):
        super().__init__(parent)
        self.api = api
        self.worker = None
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("지오코딩")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout()
        
        # 탭 위젯 생성
        tab_widget = QTabWidget()
        
        # 주소 → 좌표 탭
        self.address_tab = self.create_address_to_coord_tab()
        tab_widget.addTab(self.address_tab, "주소 → 좌표")
        
        # 좌표 → 주소 탭
        self.coord_tab = self.create_coord_to_address_tab()
        tab_widget.addTab(self.coord_tab, "좌표 → 주소")
        
        layout.addWidget(tab_widget)
        
        # 결과 표시 영역
        result_group = QGroupBox("결과")
        result_layout = QVBoxLayout()
        
        self.result_text = QTextEdit()
        self.result_text.setMaximumHeight(120)
        self.result_text.setReadOnly(True)
        
        result_layout.addWidget(self.result_text)
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        
        self.move_to_location_btn = QPushButton("지도로 이동")
        self.move_to_location_btn.clicked.connect(self.move_to_location)
        self.move_to_location_btn.setEnabled(False)
        
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(self.move_to_location_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 현재 결과 저장
        self.current_result = None
    
    def create_address_to_coord_tab(self):
        """주소 → 좌표 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 입력 그룹
        input_group = QGroupBox("주소 입력")
        input_layout = QFormLayout()
        
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("예: 서울특별시 강남구 테헤란로 152")
        self.address_input.returnPressed.connect(self.search_address)
        
        input_layout.addRow("주소:", self.address_input)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 검색 버튼
        search_btn = QPushButton("검색")
        search_btn.clicked.connect(self.search_address)
        layout.addWidget(search_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_coord_to_address_tab(self):
        """좌표 → 주소 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 입력 그룹
        input_group = QGroupBox("좌표 입력")
        input_layout = QFormLayout()
        
        # 위도 입력
        self.lat_input = QLineEdit()
        self.lat_input.setPlaceholderText("예: 37.5665")
        
        # 경도 입력  
        self.lng_input = QLineEdit()
        self.lng_input.setPlaceholderText("예: 126.9780")
        
        self.lng_input.returnPressed.connect(self.search_coordinate)
        
        input_layout.addRow("위도 (Latitude):", self.lat_input)
        input_layout.addRow("경도 (Longitude):", self.lng_input)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 검색 버튼
        search_btn = QPushButton("검색")
        search_btn.clicked.connect(self.search_coordinate)
        layout.addWidget(search_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def search_address(self):
        """주소 검색"""
        address = self.address_input.text().strip()
        if not address:
            self.result_text.setText("주소를 입력해주세요.")
            return
        
        self.result_text.setText("검색 중...")
        self.move_to_location_btn.setEnabled(False)
        
        # 워커 스레드 시작
        self.worker = GeocodingWorker(self.api, "address_to_coord", address=address)
        self.worker.result_ready.connect(self.handle_address_result)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()
    
    def search_coordinate(self):
        """좌표 검색"""
        try:
            lat = float(self.lat_input.text().strip())
            lng = float(self.lng_input.text().strip())
        except ValueError:
            self.result_text.setText("올바른 좌표를 입력해주세요.")
            return
        
        self.result_text.setText("검색 중...")
        self.move_to_location_btn.setEnabled(False)
        
        # 워커 스레드 시작
        self.worker = GeocodingWorker(self.api, "coord_to_address", x=lng, y=lat)
        self.worker.result_ready.connect(self.handle_coord_result)
        self.worker.error_occurred.connect(self.handle_error)
        self.worker.start()
    
    @pyqtSlot(dict)
    def handle_address_result(self, result):
        """주소 검색 결과 처리"""
        try:
            if 'documents' in result and result['documents']:
                doc = result['documents'][0]
                
                # 결과 표시
                display_text = f"검색 결과:\n"
                display_text += f"주소: {doc.get('address_name', 'N/A')}\n"
                display_text += f"도로명주소: {doc.get('road_address_name', 'N/A')}\n"
                display_text += f"위도: {doc.get('y', 'N/A')}\n"
                display_text += f"경도: {doc.get('x', 'N/A')}\n"
                
                self.result_text.setText(display_text)
                
                # 결과 저장
                self.current_result = {
                    'lat': float(doc.get('y', 0)),
                    'lng': float(doc.get('x', 0)),
                    'description': doc.get('address_name', '')
                }
                
                self.move_to_location_btn.setEnabled(True)
            else:
                self.result_text.setText("검색 결과가 없습니다.")
        except Exception as e:
            self.result_text.setText(f"결과 처리 중 오류: {str(e)}")
    
    @pyqtSlot(dict)
    def handle_coord_result(self, result):
        """좌표 검색 결과 처리"""
        try:
            if 'documents' in result and result['documents']:
                doc = result['documents'][0]
                
                # 결과 표시
                display_text = f"검색 결과:\n"
                
                if 'address' in doc and doc['address']:
                    addr = doc['address']
                    display_text += f"지번주소: {addr.get('address_name', 'N/A')}\n"
                
                if 'road_address' in doc and doc['road_address']:
                    road_addr = doc['road_address']
                    display_text += f"도로명주소: {road_addr.get('address_name', 'N/A')}\n"
                
                display_text += f"위도: {self.lat_input.text()}\n"
                display_text += f"경도: {self.lng_input.text()}\n"
                
                self.result_text.setText(display_text)
                
                # 결과 저장
                address_name = ""
                if 'road_address' in doc and doc['road_address']:
                    address_name = doc['road_address'].get('address_name', '')
                elif 'address' in doc and doc['address']:
                    address_name = doc['address'].get('address_name', '')
                
                self.current_result = {
                    'lat': float(self.lat_input.text()),
                    'lng': float(self.lng_input.text()),
                    'description': address_name
                }
                
                self.move_to_location_btn.setEnabled(True)
            else:
                self.result_text.setText("해당 좌표의 주소를 찾을 수 없습니다.")
        except Exception as e:
            self.result_text.setText(f"결과 처리 중 오류: {str(e)}")
    
    @pyqtSlot(str)
    def handle_error(self, error_message):
        """에러 처리"""
        self.result_text.setText(error_message)
        self.move_to_location_btn.setEnabled(False)
    
    def move_to_location(self):
        """지도로 이동"""
        if self.current_result:
            self.location_selected.emit(
                self.current_result['lat'],
                self.current_result['lng'], 
                self.current_result['description']
            )
            self.close()
    
    def closeEvent(self, event):
        """다이얼로그 종료 시 워커 스레드 정리"""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        super().closeEvent(event)