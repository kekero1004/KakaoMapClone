from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QSplitter, QMenuBar, QToolBar, QStatusBar, QMessageBox,
                             QLabel, QProgressBar, QDockWidget, QFileDialog)
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal, pyqtSlot

from ui.map_widget import MapWidget
from ui.search_widget import SearchWidget
from ui.roadview_widget import RoadviewWidget
from ui.geocoding_dialog import GeocodingDialog
from api.kakao_local_api import KakaoLocalAPI
from api.kakao_map_api import KakaoMapAPI
from api.cctv_api import CCTVApi
from utils.config import Config
from utils.cache import Cache
from models.place import Place
from models.cctv import CCTV

from typing import List, Optional
import logging


class SearchWorker(QThread):
    """검색 작업을 백그라운드에서 수행하는 워커"""
    search_completed = pyqtSignal(list)  # List[Place]
    search_failed = pyqtSignal(str)
    
    def __init__(self, local_api: KakaoLocalAPI, query: str, category: str = "", 
                 x: float = None, y: float = None, page: int = 1):
        super().__init__()
        self.local_api = local_api
        self.query = query
        self.category = category
        self.x = x
        self.y = y
        self.page = page
    
    def run(self):
        try:
            if self.category:
                places = self.local_api.search_by_category(
                    self.category, self.x, self.y, page=self.page
                )
            else:
                places = self.local_api.search_by_keyword(
                    self.query, self.x, self.y, page=self.page
                )
            
            self.search_completed.emit(places)
        except Exception as e:
            self.search_failed.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.cache = Cache()
        self.current_search_page = 1
        self.current_query = ""
        self.current_category = ""
        
        # API 초기화
        api_key = self.config.get_api_key('kakao_rest_api_key')
        js_api_key = self.config.get_api_key('kakao_javascript_api_key')
        
        if not api_key or not js_api_key:
            self.show_api_key_warning()
            return
        
        self.local_api = KakaoLocalAPI(api_key)
        self.map_api = KakaoMapAPI(api_key)
        self.cctv_api = CCTVApi()
        
        self.search_worker = None
        
        self.init_ui()
        self.setup_connections()
    
    def show_api_key_warning(self):
        """API 키 경고 메시지"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("API 키 필요")
        msg.setText("카카오 API 키가 필요합니다.")
        msg.setInformativeText("config.ini 파일에서 API 키를 설정해주세요.")
        msg.exec()
    
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("KakaoMap Clone - 카카오 지도 클론")
        
        # UI 설정 불러오기
        ui_settings = self.config.get_ui_settings()
        self.resize(ui_settings['window_width'], ui_settings['window_height'])
        
        self.setup_menu()
        self.setup_toolbar()
        self.setup_layout()
        self.setup_status_bar()
    
    def setup_menu(self):
        """메뉴바 설정"""
        menubar = self.menuBar()
        
        # 파일 메뉴
        file_menu = menubar.addMenu('파일(&F)')
        
        exit_action = QAction('종료(&X)', self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 보기 메뉴
        view_menu = menubar.addMenu('보기(&V)')
        
        self.roadview_action = QAction('로드뷰 패널', self)
        self.roadview_action.setCheckable(True)
        self.roadview_action.triggered.connect(self.toggle_roadview_panel)
        view_menu.addAction(self.roadview_action)
        
        self.search_action = QAction('검색 패널', self)
        self.search_action.setCheckable(True)
        self.search_action.setChecked(True)
        self.search_action.triggered.connect(self.toggle_search_panel)
        view_menu.addAction(self.search_action)
        
        self.roadview_split_action = QAction('로드뷰 분할화면', self)
        self.roadview_split_action.setCheckable(True)
        self.roadview_split_action.triggered.connect(self.toggle_roadview_split)
        view_menu.addAction(self.roadview_split_action)
        
        # 도구 메뉴
        tools_menu = menubar.addMenu('도구(&T)')
        
        # 지오코딩 액션
        geocoding_action = QAction('지오코딩', self)
        geocoding_action.triggered.connect(self.open_geocoding_dialog)
        tools_menu.addAction(geocoding_action)
        
        tools_menu.addSeparator()
        
        clear_cache_action = QAction('캐시 정리', self)
        clear_cache_action.triggered.connect(self.clear_cache)
        tools_menu.addAction(clear_cache_action)
        
        tools_menu.addSeparator()
        
        # SHP 파일 관련 액션
        load_shp_action = QAction('SHP 파일 불러오기', self)
        load_shp_action.triggered.connect(self.load_shp_file)
        tools_menu.addAction(load_shp_action)
        
        self.clear_shp_action = QAction('SHP 레이어 제거', self)
        self.clear_shp_action.triggered.connect(self.clear_shp_layers)
        self.clear_shp_action.setEnabled(False)
        tools_menu.addAction(self.clear_shp_action)
        
        # 지도 메뉴
        map_menu = menubar.addMenu('지도(&M)')
        
        # 지도 타입 액션들
        self.normal_map_action = QAction('일반 지도', self)
        self.normal_map_action.setCheckable(True)
        self.normal_map_action.setChecked(True)
        self.normal_map_action.triggered.connect(lambda: self.change_map_type('ROADMAP'))
        
        self.satellite_map_action = QAction('위성 지도', self)
        self.satellite_map_action.setCheckable(True)
        self.satellite_map_action.triggered.connect(lambda: self.change_map_type('SATELLITE'))
        
        self.hybrid_map_action = QAction('하이브리드 지도', self)
        self.hybrid_map_action.setCheckable(True)
        self.hybrid_map_action.triggered.connect(lambda: self.change_map_type('HYBRID'))
        
        map_menu.addAction(self.normal_map_action)
        map_menu.addAction(self.satellite_map_action)
        map_menu.addAction(self.hybrid_map_action)
        map_menu.addSeparator()
        
        
        # 도움말 메뉴
        help_menu = menubar.addMenu('도움말(&H)')
        
        about_action = QAction('정보(&A)', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """툴바 설정"""
        # 기본 도구 모음
        basic_toolbar = QToolBar("기본 도구")
        basic_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, basic_toolbar)
        
        # 지도 확대/축소 버튼
        #zoom_in_action = QAction('🔍+', self)
        #zoom_in_action.setText("확대")
        #zoom_in_action.setToolTip("지도 확대")
        #zoom_in_action.triggered.connect(self.zoom_in)
        #basic_toolbar.addAction(zoom_in_action)
        
        #zoom_out_action = QAction('🔍-', self)
        #zoom_out_action.setText("축소")
        #zoom_out_action.setToolTip("지도 축소")
        #zoom_out_action.triggered.connect(self.zoom_out)
        #basic_toolbar.addAction(zoom_out_action)
        
        #basic_toolbar.addSeparator()
        
        # 현재 위치 버튼
        current_location_action = QAction('📍', self)
        current_location_action.setText("현재위치")
        current_location_action.setToolTip("현재 위치로 이동")
        current_location_action.triggered.connect(self.go_to_current_location)
        basic_toolbar.addAction(current_location_action)
        
        # 로드뷰 버튼
        self.roadview_toggle_action = QAction('🛣️', self)
        self.roadview_toggle_action.setText("로드뷰")
        self.roadview_toggle_action.setToolTip("로드뷰 모드 토글")
        self.roadview_toggle_action.setCheckable(True)
        self.roadview_toggle_action.triggered.connect(self.toggle_roadview_mode)
        basic_toolbar.addAction(self.roadview_toggle_action)
        
        # CCTV 토글 버튼
        self.cctv_action = QAction('📹', self)
        self.cctv_action.setText("CCTV")
        self.cctv_action.setCheckable(True)
        self.cctv_action.triggered.connect(self.toggle_cctv_markers)
        basic_toolbar.addAction(self.cctv_action)
        
        # 측정 도구 툴바
        measure_toolbar = QToolBar("측정 도구")
        measure_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, measure_toolbar)
        
        # 거리 측정 버튼
        self.distance_measure_action = QAction('📏', self)
        self.distance_measure_action.setText("거리측정")
        self.distance_measure_action.setToolTip("거리 측정")
        self.distance_measure_action.setCheckable(True)
        self.distance_measure_action.triggered.connect(self.start_distance_measurement)
        measure_toolbar.addAction(self.distance_measure_action)
        
        # 면적 측정 버튼
        self.area_measure_action = QAction('📐', self)
        self.area_measure_action.setText("면적측정")
        self.area_measure_action.setToolTip("면적 측정")
        self.area_measure_action.setCheckable(True)
        self.area_measure_action.triggered.connect(self.start_area_measurement)
        measure_toolbar.addAction(self.area_measure_action)
        
        # 측정 초기화 버튼
        clear_measure_action = QAction('🗑️', self)
        clear_measure_action.setText("측정초기화")
        clear_measure_action.setToolTip("모든 측정 결과 지우기")
        clear_measure_action.triggered.connect(self.clear_measurements)
        measure_toolbar.addAction(clear_measure_action)
        
        # 도구 툴바 추가
        tools_toolbar = QToolBar("도구")
        tools_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tools_toolbar)
        
        # 드로잉 툴박스 버튼
        self.drawing_toolbox_action = QAction('✏️', self)
        self.drawing_toolbox_action.setText("그리기도구")
        self.drawing_toolbox_action.setToolTip("드로잉 툴박스 토글")
        self.drawing_toolbox_action.setCheckable(True)
        self.drawing_toolbox_action.triggered.connect(self.toggle_drawing_toolbox)
        tools_toolbar.addAction(self.drawing_toolbox_action)
    
    def setup_layout(self):
        """레이아웃 설정"""
        # 지도 위젯을 메인 중앙 위젯으로 설정
        js_api_key = self.config.get_api_key('kakao_javascript_api_key')
        self.map_widget = MapWidget(js_api_key)
        self.setCentralWidget(self.map_widget)
        
        # 검색 패널을 왼쪽 도크 위젯으로 설정
        self.search_widget = SearchWidget()
        self.search_dock = QDockWidget("검색", self)
        self.search_dock.setWidget(self.search_widget)
        self.search_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.search_dock)
        
        # 로드뷰 위젯은 독립적으로 관리
        self.roadview_widget = RoadviewWidget(js_api_key)
        self.roadview_widget.hide()
        
        # 로드뷰 분할화면을 위한 스플리터 준비
        self.roadview_splitter = None
    
    def setup_status_bar(self):
        """상태바 설정"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 상태 라벨
        self.status_label = QLabel("준비")
        self.status_bar.addWidget(self.status_label)
        
        # 프로그레스 바
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # 좌표 라벨
        self.coord_status_label = QLabel("위도: 37.5665, 경도: 126.9780")
        self.status_bar.addPermanentWidget(self.coord_status_label)
    
    def setup_connections(self):
        """시그널-슬롯 연결"""
        # 검색 위젯 연결
        self.search_widget.search_requested.connect(self.on_search_requested)
        self.search_widget.place_selected.connect(self.on_place_selected)
        self.search_widget.category_selected.connect(self.on_category_selected)
        
        # 지도 위젯 연결
        self.map_widget.location_clicked.connect(self.on_location_clicked)
        self.map_widget.marker_clicked.connect(self.on_marker_clicked)
        self.map_widget.roadview_clicked.connect(self.open_roadview_popup)
        
        # 로드뷰 위젯 연결
        self.roadview_widget.roadview_closed.connect(self.on_roadview_closed)
        self.roadview_widget.roadview_moved.connect(self.on_roadview_moved)
    
    @pyqtSlot(str, str)
    def on_search_requested(self, query: str, category: str):
        """검색 요청 처리"""
        if query.endswith(":next_page"):
            # 다음 페이지 요청
            self.current_search_page += 1
            query = query.replace(":next_page", "")
        else:
            # 새로운 검색
            self.current_search_page = 1
            self.current_query = query
            self.current_category = category
        
        self.status_label.setText("검색 중...")
        self.progress_bar.show()
        
        # 현재 지도 중심점 가져오기
        center = self.map_widget.current_center
        
        # 백그라운드에서 검색 수행
        self.search_worker = SearchWorker(
            self.local_api, query, category, 
            center['lng'], center['lat'], self.current_search_page
        )
        self.search_worker.search_completed.connect(self.on_search_completed)
        self.search_worker.search_failed.connect(self.on_search_failed)
        self.search_worker.start()
    
    @pyqtSlot(list)
    def on_search_completed(self, places: List[Place]):
        """검색 완료 처리"""
        self.progress_bar.hide()
        
        if places:
            append_results = self.current_search_page > 1
            self.search_widget.update_results(places, append_results)
            
            # 첫 번째 검색 결과로 지도 이동 (첫 페이지만)
            if not append_results and places:
                first_place = places[0]
                self.map_widget.set_center(first_place.y, first_place.x)
            
            # 지도에 마커 추가
            for place in places:
                marker_id = f"place_{place.id}"
                self.map_widget.add_marker(
                    marker_id, place.y, place.x, 
                    place.name, place.get_display_address()
                )
            
            self.status_label.setText(f"검색 완료: {len(places)}개 결과")
        else:
            self.status_label.setText("검색 결과가 없습니다")
    
    @pyqtSlot(str)
    def on_search_failed(self, error_message: str):
        """검색 실패 처리"""
        self.progress_bar.hide()
        self.status_label.setText(f"검색 실패: {error_message}")
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("검색 오류")
        msg.setText("검색 중 오류가 발생했습니다.")
        msg.setInformativeText(error_message)
        msg.exec()
    
    @pyqtSlot(Place)
    def on_place_selected(self, place: Place):
        """장소 선택 처리"""
        self.map_widget.set_center(place.y, place.x)
        self.map_widget.set_zoom(3)  # 확대
        self.status_label.setText(f"선택됨: {place.name}")
        
        # 좌표 상태바 업데이트
        self.coord_status_label.setText(f"위도: {place.y:.6f}, 경도: {place.x:.6f}")
    
    @pyqtSlot(str, str)
    def on_category_selected(self, category_code: str, category_name: str):
        """카테고리 선택 처리"""
        center = self.map_widget.current_center
        self.on_search_requested("", category_code)
    
    @pyqtSlot(float, float)
    def on_location_clicked(self, lat: float, lng: float):
        """지도 클릭 처리"""
        self.coord_status_label.setText(f"위도: {lat:.6f}, 경도: {lng:.6f}")
        
        # 로드뷰 열기
        self.roadview_widget.load_roadview(lng, lat)
        # MapWalker 생성
        self.map_widget.create_map_walker(lat, lng, 0)
        if not self.roadview_action.isChecked():
            self.roadview_action.setChecked(True)
    
    @pyqtSlot(str)
    def on_marker_clicked(self, marker_id: str):
        """마커 클릭 처리"""
        self.status_label.setText(f"마커 클릭: {marker_id}")
    
    def toggle_roadview_panel(self):
        """로드뷰 패널 토글"""
        if self.roadview_action.isChecked():
            self.roadview_widget.show()
        else:
            self.roadview_widget.hide()
    
    def toggle_search_panel(self):
        """검색 패널 토글"""
        if self.search_action.isChecked():
            self.search_dock.show()
        else:
            self.search_dock.hide()
    
    def toggle_roadview_split(self):
        """로드뷰 분할화면 토글"""
        if self.roadview_split_action.isChecked():
            self.enable_roadview_split()
        else:
            self.disable_roadview_split()
    
    def enable_roadview_split(self):
        """로드뷰 분할화면 활성화"""
        if not self.roadview_splitter:
            # 현재 중앙 위젯(지도)을 제거
            current_central = self.centralWidget()
            
            # 스플리터 생성
            self.roadview_splitter = QSplitter(Qt.Orientation.Horizontal)
            self.roadview_splitter.addWidget(current_central)
            self.roadview_splitter.addWidget(self.roadview_widget)
            
            # 스플리터를 중앙 위젯으로 설정
            self.setCentralWidget(self.roadview_splitter)
            
            # 비율 설정 (지도 70%, 로드뷰 30%)
            self.roadview_splitter.setSizes([700, 300])
            
            self.roadview_widget.show()
    
    def disable_roadview_split(self):
        """로드뷰 분할화면 비활성화"""
        if self.roadview_splitter:
            # 지도 위젯을 다시 중앙 위젯으로 설정
            map_widget = self.roadview_splitter.widget(0)
            self.setCentralWidget(map_widget)
            
            # 로드뷰 위젯 숨기기
            self.roadview_widget.hide()
            
            # 스플리터 제거
            self.roadview_splitter = None
    
    def toggle_cctv_markers(self):
        """CCTV 마커 토글"""
        if self.cctv_action.isChecked():
            self.load_cctv_markers()
        else:
            self.clear_cctv_markers()
    
    def load_cctv_markers(self):
        """CCTV 마커 로드"""
        center = self.map_widget.current_center
        
        try:
            # 주변 CCTV 검색 (1km 반경)
            cctvs = self.cctv_api.get_cctv_list(center['lng'], center['lat'], 1.0)
            
            for cctv in cctvs:
                marker_id = f"cctv_{cctv.id}"
                self.map_widget.add_marker(
                    marker_id, cctv.y, cctv.x,
                    cctv.get_display_name(),
                    f"📹 {cctv.purpose} CCTV\n{cctv.address}"
                )
            
            self.status_label.setText(f"CCTV {len(cctvs)}개 표시")
        except Exception as e:
            self.status_label.setText(f"CCTV 로드 실패: {str(e)}")
    
    def clear_cctv_markers(self):
        """CCTV 마커 제거"""
        # CCTV 마커만 제거 (place_ 마커는 유지)
        for marker_id in list(self.map_widget.markers.keys()):
            if marker_id.startswith("cctv_"):
                self.map_widget.remove_marker(marker_id)
    
    def go_to_current_location(self):
        """현재 위치로 이동"""
        map_settings = self.config.get_map_settings()
        self.map_widget.set_center(map_settings['default_lat'], map_settings['default_lng'])
        self.status_label.setText("기본 위치로 이동")
    
    def open_roadview_at_center(self):
        """현재 지도 중심에서 로드뷰 열기"""
        center = self.map_widget.current_center
        self.roadview_widget.load_roadview(center['lng'], center['lat'])
        self.roadview_action.setChecked(True)
    
    def on_roadview_closed(self):
        """로드뷰 닫힘 처리"""
        self.roadview_action.setChecked(False)
        # MapWalker와 원형 마커 제거
        self.map_widget.remove_map_walker()
        self.map_widget.remove_roadview_circle_marker()
    
    @pyqtSlot(float, float, float)
    def on_roadview_moved(self, lat: float, lng: float, angle: float):
        """로드뷰 위치/각도 변경 처리"""
        # MapWalker와 원형 마커 업데이트
        self.map_widget.move_map_walker(lat, lng, angle)
        self.map_widget.move_roadview_circle_marker(lat, lng)
    
    def open_geocoding_dialog(self):
        """지오코딩 다이얼로그 열기"""
        dialog = GeocodingDialog(self.map_api, self)
        dialog.location_selected.connect(self.on_geocoding_location_selected)
        dialog.exec()
    
    def on_geocoding_location_selected(self, lat: float, lng: float, description: str):
        """지오코딩 결과 위치로 이동"""
        self.map_widget.set_center(lat, lng)
        self.map_widget.add_marker("geocoding_result", lat, lng, "지오코딩 결과", description)
        self.status_label.setText(f"지오코딩 결과: {description}")
    
    def clear_cache(self):
        """캐시 정리"""
        self.cache.clear()
        self.status_label.setText("캐시가 정리되었습니다")
    
    def show_about(self):
        """정보 대화상자"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("정보")
        msg.setText("KakaoMap Clone")
        msg.setInformativeText("Python PyQt6과 카카오맵 API를 이용한 지도 애플리케이션")
        msg.exec()
    
    # 지도 컨트롤 메서드들
    def zoom_in(self):
        """지도 확대"""
        if hasattr(self, 'map_widget'):
            self.map_widget.zoom_in()
    
    def zoom_out(self):
        """지도 축소"""
        if hasattr(self, 'map_widget'):
            self.map_widget.zoom_out()
    
    def change_map_type(self, map_type):
        """지도 타입 변경"""
        if hasattr(self, 'map_widget'):
            self.map_widget.change_map_type(map_type)
            
            # 메뉴 체크 상태 업데이트
            self.normal_map_action.setChecked(map_type == 'ROADMAP')
            self.satellite_map_action.setChecked(map_type == 'SATELLITE')
            self.hybrid_map_action.setChecked(map_type == 'HYBRID')
            
            self.status_label.setText(f"지도 타입 변경: {map_type}")
    
    def start_distance_measurement(self):
        """거리 측정 시작"""
        if self.distance_measure_action.isChecked():
            # 면적 측정 끄기
            self.area_measure_action.setChecked(False)
            self.map_widget.start_distance_measurement()
            self.status_label.setText("거리 측정 모드: 지도를 클릭하여 거리를 측정하세요")
        else:
            self.map_widget.stop_measurement()
            self.status_label.setText("거리 측정 모드 종료")
    
    def start_area_measurement(self):
        """면적 측정 시작"""
        if self.area_measure_action.isChecked():
            # 거리 측정 끄기
            self.distance_measure_action.setChecked(False)
            self.map_widget.start_area_measurement()
            self.status_label.setText("면적 측정 모드: 지도를 클릭하여 면적을 측정하세요")
        else:
            self.map_widget.stop_measurement()
            self.status_label.setText("면적 측정 모드 종료")
    
    def clear_measurements(self):
        """모든 측정 결과 지우기"""
        self.distance_measure_action.setChecked(False)
        self.area_measure_action.setChecked(False)
        self.map_widget.clear_measurements()
        self.status_label.setText("측정 결과가 초기화되었습니다")
    
    def toggle_roadview_mode(self):
        """로드뷰 모드 토글"""
        if self.roadview_toggle_action.isChecked():
            self.map_widget.enable_roadview_mode()
            self.status_label.setText("로드뷰 모드: 도로 표시 활성화 - 로드뷰 가능 구간을 클릭하세요")
        else:
            self.map_widget.disable_roadview_mode()
            self.status_label.setText("로드뷰 모드 해제 - 도로 표시 비활성화")
    
    def open_roadview_popup(self, lat, lng):
        """로드뷰 팝업 열기"""
        # 클릭된 지점에 즉시 MapWalker와 원형 마커 생성
        self.map_widget.create_map_walker(lat, lng, 0)
        self.map_widget.create_roadview_circle_marker(lat, lng)
        
        self.roadview_widget.load_roadview(lng, lat)
        if not self.roadview_split_action.isChecked():
            # 분할화면이 아닌 경우 팝업으로 표시
            self.roadview_widget.show()
            self.roadview_widget.raise_()
        else:
            # 분할화면인 경우는 이미 표시됨
            pass
    
    def load_shp_file(self):
        """SHP 파일 불러오기"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "SHP 파일 선택",
            "",
            "Shapefile (*.shp);;All Files (*)"
        )
        
        if file_path:
            try:
                self.map_widget.load_shapefile(file_path)
                self.clear_shp_action.setEnabled(True)
                self.status_label.setText(f"SHP 파일 로드됨: {file_path.split('/')[-1]}")
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "SHP 파일 로드 오류",
                    f"파일을 로드할 수 없습니다: {str(e)}"
                )
                self.status_label.setText(f"SHP 파일 로드 실패: {str(e)}")
    
    def clear_shp_layers(self):
        """SHP 레이어 제거"""
        self.map_widget.clear_shapefile_layers()
        self.clear_shp_action.setEnabled(False)
        self.status_label.setText("SHP 레이어가 제거되었습니다")
    
    def toggle_drawing_toolbox(self):
        """드로잉 툴박스 토글"""
        if self.drawing_toolbox_action.isChecked():
            self.map_widget.toggle_drawing_toolbox()
            self.status_label.setText("드로잉 툴박스 활성화 - 지도에서 도구를 선택하여 그리기")
        else:
            self.map_widget.toggle_drawing_toolbox()
            self.status_label.setText("드로잉 툴박스 비활성화")
    
    def closeEvent(self, event):
        """애플리케이션 종료 시 설정 저장"""
        # 윈도우 크기 저장
        self.config.set_ui_settings(
            window_width=self.width(),
            window_height=self.height()
        )
        
        # 워커 스레드 정리
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.quit()
            self.search_worker.wait()
        
        event.accept()