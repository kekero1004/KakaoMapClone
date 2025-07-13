from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QListWidget, QPushButton, QComboBox, QLabel, 
                             QListWidgetItem, QFrame, QScrollArea)
from PyQt6.QtCore import pyqtSignal, Qt, QThread, pyqtSlot
from PyQt6.QtGui import QFont
from typing import List, Optional
from models.place import Place


class SearchResultItem(QWidget):
    """검색 결과 아이템 위젯"""
    def __init__(self, place: Place):
        super().__init__()
        self.place = place
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 장소명
        name_label = QLabel(self.place.name)
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(10)
        name_label.setFont(name_font)
        layout.addWidget(name_label)
        
        # 카테고리
        if self.place.category:
            category_label = QLabel(self.place.get_short_category())
            category_label.setStyleSheet("color: #666666; font-size: 9px;")
            layout.addWidget(category_label)
        
        # 주소
        address_label = QLabel(self.place.get_display_address())
        address_label.setStyleSheet("color: #888888; font-size: 9px;")
        address_label.setWordWrap(True)
        layout.addWidget(address_label)
        
        # 전화번호
        if self.place.has_phone():
            phone_label = QLabel(f"📞 {self.place.phone}")
            phone_label.setStyleSheet("color: #0066cc; font-size: 9px;")
            layout.addWidget(phone_label)
        
        # 거리 정보
        if self.place.distance:
            distance_label = QLabel(f"📍 {self.place.distance:.0f}m")
            distance_label.setStyleSheet("color: #ff6600; font-size: 9px;")
            layout.addWidget(distance_label)
        
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #eeeeee;")
        layout.addWidget(line)
        
        self.setLayout(layout)


class SearchWidget(QWidget):
    search_requested = pyqtSignal(str, str)  # query, category
    place_selected = pyqtSignal(Place)
    category_selected = pyqtSignal(str, str)  # category_code, category_name
    
    def __init__(self):
        super().__init__()
        self.current_places = []
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.setup_search_input(layout)
        self.setup_category_filter(layout)
        self.setup_result_list(layout)
        
        self.setLayout(layout)
        self.setMinimumWidth(300)
    
    def setup_search_input(self, layout):
        """검색 입력 필드 설정"""
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("장소, 주소 검색...")
        self.search_input.returnPressed.connect(self.perform_search)
        
        self.search_btn = QPushButton("검색")
        self.search_btn.clicked.connect(self.perform_search)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        
        layout.addLayout(search_layout)
    
    def setup_category_filter(self, layout):
        """카테고리 필터 설정"""
        category_layout = QVBoxLayout()
        
        category_label = QLabel("카테고리")
        category_label.setFont(QFont("", 9, QFont.Weight.Bold))
        category_layout.addWidget(category_label)
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("전체", "")
        self.category_combo.addItem("🏪 대형마트", "MT1")
        self.category_combo.addItem("🏪 편의점", "CS2")
        self.category_combo.addItem("🎓 학교", "SC4")
        self.category_combo.addItem("🅿️ 주차장", "PK6")
        self.category_combo.addItem("⛽ 주유소", "OL7")
        self.category_combo.addItem("🚇 지하철역", "SW8")
        self.category_combo.addItem("🏦 은행", "BK9")
        self.category_combo.addItem("🎭 문화시설", "CT1")
        self.category_combo.addItem("🏛️ 공공기관", "PO3")
        self.category_combo.addItem("🗼 관광명소", "AT4")
        self.category_combo.addItem("🏨 숙박", "AD5")
        self.category_combo.addItem("🍽️ 음식점", "FD6")
        self.category_combo.addItem("☕ 카페", "CE7")
        self.category_combo.addItem("🏥 병원", "HP8")
        self.category_combo.addItem("💊 약국", "PM9")
        
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        category_layout.addWidget(self.category_combo)
        
        layout.addLayout(category_layout)
    
    def setup_result_list(self, layout):
        """검색 결과 리스트 설정"""
        result_label = QLabel("검색 결과")
        result_label.setFont(QFont("", 9, QFont.Weight.Bold))
        layout.addWidget(result_label)
        
        self.result_count_label = QLabel("검색을 시작하세요")
        self.result_count_label.setStyleSheet("color: #666666; font-size: 9px;")
        layout.addWidget(self.result_count_label)
        
        # 스크롤 가능한 결과 영역
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.result_widget = QWidget()
        self.result_layout = QVBoxLayout(self.result_widget)
        self.result_layout.setContentsMargins(0, 0, 0, 0)
        self.result_layout.addStretch()
        
        self.scroll_area.setWidget(self.result_widget)
        layout.addWidget(self.scroll_area)
        
        # 더보기 버튼
        self.load_more_btn = QPushButton("더보기")
        self.load_more_btn.clicked.connect(self.load_more_results)
        self.load_more_btn.hide()
        layout.addWidget(self.load_more_btn)
    
    def perform_search(self):
        """검색 실행"""
        query = self.search_input.text().strip()
        if not query:
            return
        
        current_category = self.category_combo.currentData()
        self.search_requested.emit(query, current_category or "")
    
    def on_category_changed(self):
        """카테고리 변경 시 처리"""
        category_code = self.category_combo.currentData()
        category_name = self.category_combo.currentText()
        
        if category_code:
            self.category_selected.emit(category_code, category_name)
    
    def update_results(self, places: List[Place], append: bool = False):
        """검색 결과 업데이트"""
        if not append:
            self.clear_results()
            self.current_places = places.copy()
        else:
            self.current_places.extend(places)
        
        # 결과 개수 업데이트
        count = len(self.current_places)
        if count == 0:
            self.result_count_label.setText("검색 결과가 없습니다")
        else:
            self.result_count_label.setText(f"총 {count}개 결과")
        
        # 새로운 결과들 추가
        for place in places:
            item_widget = SearchResultItem(place)
            item_widget.mousePressEvent = lambda event, p=place: self.on_place_clicked(p)
            item_widget.setStyleSheet("QWidget:hover { background-color: #f0f0f0; }")
            
            # 마지막 stretch 제거 후 위젯 추가
            last_item = self.result_layout.takeAt(self.result_layout.count() - 1)
            self.result_layout.addWidget(item_widget)
            if last_item:
                self.result_layout.addItem(last_item)
        
        # 더보기 버튼 표시 여부
        if len(places) >= 15:  # 한 페이지 최대 결과 수
            self.load_more_btn.show()
        else:
            self.load_more_btn.hide()
    
    def clear_results(self):
        """검색 결과 초기화"""
        while self.result_layout.count() > 1:  # stretch 제외하고 모든 위젯 제거
            child = self.result_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.current_places.clear()
        self.load_more_btn.hide()
    
    def on_place_clicked(self, place: Place):
        """장소 클릭 시 처리"""
        self.place_selected.emit(place)
    
    def load_more_results(self):
        """더많은 결과 로드"""
        query = self.search_input.text().strip()
        category = self.category_combo.currentData()
        
        # 다음 페이지 요청 (페이지 번호는 부모에서 관리)
        self.search_requested.emit(f"{query}:next_page", category or "")
    
    def set_search_text(self, text: str):
        """검색어 설정"""
        self.search_input.setText(text)
    
    def get_current_search_text(self) -> str:
        """현재 검색어 반환"""
        return self.search_input.text().strip()
    
    def get_current_category(self) -> str:
        """현재 선택된 카테고리 반환"""
        return self.category_combo.currentData() or ""