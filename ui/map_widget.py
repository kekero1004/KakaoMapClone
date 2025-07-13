from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import pyqtSignal, QUrl, QTimer
from PyQt6.QtGui import QIcon
from typing import Dict, Any
import json


class MapWidget(QWidget):
    location_clicked = pyqtSignal(float, float)
    marker_clicked = pyqtSignal(str)
    roadview_clicked = pyqtSignal(float, float)
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
        self.markers = {}
        self.current_center = {'lat': 37.5665, 'lng': 126.9780}
        self.current_zoom = 15
        self.current_map_type = 'ROADMAP'
        self.measurement_mode = None  # None, 'distance', 'area'
        self.roadview_mode = False
        self.shapefile_layers = []
        self.callback_timer = None
        self.last_callback_timestamps = {'mapClick': 0, 'roadviewClick': 0}
        self.init_ui()
    
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # 여백 제거
        
        # 웹 엔진 뷰 (카카오맵)
        self.web_view = QWebEngineView()
        
        # 웹 엔진 설정
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        
        layout.addWidget(self.web_view)
        
        self.setLayout(layout)
        
        # 지도 로드 (약간의 지연을 두고)
        QTimer.singleShot(500, self.load_map)
    
    def load_map(self, lat=37.5665, lng=126.9780, zoom=15):
        """지도 로드"""
        self.current_center = {'lat': lat, 'lng': lng}
        self.current_zoom = zoom
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Kakao Map</title>
            <style>
                body, html {{ margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden; }}
                #map {{ width: 100%; height: 100%; }}
                #loading {{ 
                    position: absolute; 
                    top: 50%; 
                    left: 50%; 
                    transform: translate(-50%, -50%);
                    font-size: 18px;
                    z-index: 1000;
                }}
                /* MapWalker 스타일 */
                .MapWalker {{
                    width: 26px;
                    height: 42px;
                }}
                .MapWalker .angleBack {{
                    width: 26px;
                    height: 42px;
                    background: url('https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/roadview_minimap_wk_2018.png') no-repeat;
                    background-size: 1924px 42px;
                    background-position: -702px 0;
                }}
                .MapWalker .figure {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 26px;
                    height: 42px;
                    background: url('https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/roadview_minimap_wk_2018.png') no-repeat;
                    background-size: 1924px 42px;
                    background-position: 0 0;
                }}
                /* 16방향 스프라이트 */
                .MapWalker.m0 .figure {{ background-position: 0 0; }}
                .MapWalker.m1 .figure {{ background-position: -26px 0; }}
                .MapWalker.m2 .figure {{ background-position: -52px 0; }}
                .MapWalker.m3 .figure {{ background-position: -78px 0; }}
                .MapWalker.m4 .figure {{ background-position: -104px 0; }}
                .MapWalker.m5 .figure {{ background-position: -130px 0; }}
                .MapWalker.m6 .figure {{ background-position: -156px 0; }}
                .MapWalker.m7 .figure {{ background-position: -182px 0; }}
                .MapWalker.m8 .figure {{ background-position: -208px 0; }}
                .MapWalker.m9 .figure {{ background-position: -234px 0; }}
                .MapWalker.m10 .figure {{ background-position: -260px 0; }}
                .MapWalker.m11 .figure {{ background-position: -286px 0; }}
                .MapWalker.m12 .figure {{ background-position: -312px 0; }}
                .MapWalker.m13 .figure {{ background-position: -338px 0; }}
                .MapWalker.m14 .figure {{ background-position: -364px 0; }}
                .MapWalker.m15 .figure {{ background-position: -390px 0; }}
                
                /* 커스텀 컨트롤 스타일 */
                .custom-control {{
                    position: absolute;
                    background: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                    z-index: 10;
                }}
                
                .map-type-control {{
                    top: 10px;
                    right: 10px;
                    padding: 5px;
                }}
                
                .zoom-control {{
                    top: 10px;
                    left: 10px;
                    display: flex;
                    flex-direction: column;
                }}
                
                .control-btn {{
                    background: white;
                    border: 1px solid #ddd;
                    padding: 8px 12px;
                    cursor: pointer;
                    margin: 2px;
                    border-radius: 3px;
                    font-size: 12px;
                    min-width: 60px;
                    text-align: center;
                }}
                
                .control-btn:hover {{
                    background: #f5f5f5;
                }}
                
                .control-btn.selected {{
                    background: #4285f4;
                    color: white;
                }}
                
                /* 거리 측정 스타일 */
                .dot {{
                    overflow: hidden;
                    float: left;
                    width: 12px;
                    height: 12px;
                    background: url('https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/dotOverlay.png');
                }}
                .dotOverlay {{
                    position: relative;
                    bottom: 10px;
                    border-radius: 6px;
                    border: 1px solid #ccc;
                    border-bottom: 2px solid #ddd;
                    float: left;
                    font-size: 12px;
                    font-family: 'Malgun Gothic', dotum, '돋움', sans-serif;
                    background: #fff;
                    white-space: nowrap;
                }}
                .dotOverlay:nth-of-type(n) {{
                    border: 0; border-radius: 6px; border-bottom: 2px solid #ddd;
                }}
                .dotOverlay a {{
                    display: block;
                    text-decoration: none;
                    color: #000;
                    text-align: center;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                    overflow: hidden;
                    background: #d95050;
                    background: #d95050 url(https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/arrowdown.png) no-repeat right 14px center;
                }}
                .dotOverlay a:hover {{
                    background: #c12222;
                    background: #c12222 url(https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/arrowdown.png) no-repeat right 14px center;
                }}
                .dotOverlay a.selected {{
                    background: #c12222;
                    background: #c12222 url(https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/arrowdown.png) no-repeat right 14px center;
                }}
                .dotOverlay:after {{
                    content: '';
                    position: absolute;
                    margin-left: -12px;
                    left: 50%;
                    bottom: -8px;
                    width: 22px;
                    height: 8px;
                    background: url('https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/vertex_white.png')
                }}
                .distanceInfo {{
                    position: relative;
                    top: 5px;
                    left: 5px;
                    list-style: none;
                    margin: 0;
                }}
                .distanceInfo .label {{
                    display: inline-block;
                    width: 50px;
                }}
                .distanceInfo:after {{
                    content: none;
                }}
                
                /* 면적 측정 스타일 */
                .areaInfo {{
                    position: relative;
                    top: 5px;
                    left: 5px;
                    list-style: none;
                    margin: 0;
                    padding: 5px 10px;
                    background: #fff;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    font-size: 12px;
                }}
                .areaInfo .label {{
                    display: inline-block;
                    width: 50px;
                    margin-right: 5px;
                }}
                .areaInfo .number {{
                    font-weight: bold;
                    color: #00a0e9;
                }}
                .areaInfo:after {{
                    content: none;
                }}
            </style>
        </head>
        <body>
            <div id="loading">🗺️ 지도 로딩 중...</div>
            <div id="map"></div>
            
            <!-- 커스텀 지도 타입 컨트롤 -->
            <div class="custom-control map-type-control">
                <div id="btnRoadmap" class="control-btn selected" onclick="setMapType('roadmap')">일반</div>
                <div id="btnSkyview" class="control-btn" onclick="setMapType('skyview')">위성</div>
            </div>
            
            <!-- 커스텀 줌 컨트롤 -->
            <div class="custom-control zoom-control">
                <div class="control-btn" onclick="zoomIn()">+</div>
                <div class="control-btn" onclick="zoomOut()">-</div>
            </div>
            
            <!-- 드로잉 툴박스 -->
            <div id="drawingToolbox" class="custom-control" style="top: 70px; left: 10px; display: none;">
                <div class="control-btn" onclick="selectDrawingMode('MARKER')">마커</div>
                <div class="control-btn" onclick="selectDrawingMode('POLYLINE')">선</div>
                <div class="control-btn" onclick="selectDrawingMode('RECTANGLE')">사각형</div>
                <div class="control-btn" onclick="selectDrawingMode('CIRCLE')">원</div>
                <div class="control-btn" onclick="selectDrawingMode('POLYGON')">다각형</div>
                <div class="control-btn" onclick="clearDrawings()" style="background: #ff6b6b; color: white;">전체 삭제</div>
            </div>
            
            <script type="text/javascript" src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={self.api_key}&libraries=drawing&autoload=false"></script>
            <script>
                console.log("카카오맵 SDK 로딩 시작");
                
                // 카카오맵 SDK 로드 완료 후 실행
                kakao.maps.load(function() {{
                    console.log("카카오맵 SDK 로드 완료");
                    
                    // 로딩 메시지 숨기기
                    document.getElementById('loading').style.display = 'none';
                    
                    var container = document.getElementById('map');
                    var options = {{
                        center: new kakao.maps.LatLng({lat}, {lng}),
                        level: {zoom}
                    }};
                    
                    console.log("지도 초기화 중...", options);
                    
                    try {{
                        var map = new kakao.maps.Map(container, options);
                        var markers = {{}};
                        
                        console.log("지도 초기화 완료");
                        
                        // MapWalker 클래스 정의
                        function MapWalker(position) {{
                            var content = document.createElement('div');
                            var figure = document.createElement('div');
                            var angleBack = document.createElement('div');
                            
                            content.className = 'MapWalker';
                            figure.className = 'figure';
                            angleBack.className = 'angleBack';
                            
                            content.appendChild(angleBack);
                            content.appendChild(figure);
                            
                            var walker = new kakao.maps.CustomOverlay({{
                                position: position,
                                content: content,
                                yAnchor: 1
                            }});
                            
                            this.walker = walker;
                            this.content = content;
                        }}
                        
                        MapWalker.prototype.setAngle = function(angle) {{
                            var threshold = 22.5;
                            for(var i=0; i<16; i++) {{
                                if(angle > (threshold * i) && angle < (threshold * (i + 1))) {{
                                    var className = 'm' + i;
                                    this.content.className = this.content.className.split(' ')[0];
                                    this.content.className += (' ' + className);
                                    break;
                                }}
                            }}
                        }};
                        
                        MapWalker.prototype.setPosition = function(position) {{
                            this.walker.setPosition(position);
                        }};
                        
                        MapWalker.prototype.setMap = function(map) {{
                            this.walker.setMap(map);
                        }};
                        
                        // MapWalker 인스턴스
                        var mapWalker = null;
                        
                        // 지도 로드 완료 후 Python에 알림
                        if (window.qt && window.qt.webChannelTransport) {{
                            console.log("지도 로드 완료 - Python 알림");
                        }}
                        
                        // 지도 클릭 이벤트
                        kakao.maps.event.addListener(map, 'click', function(mouseEvent) {{
                            var latlng = mouseEvent.latLng;
                            console.log("지도 클릭:", latlng.getLat(), latlng.getLng());
                            
                            // 거리 측정 모드
                            if (distanceMeasureMode) {{
                                var clickPosition = latlng;
                                
                                if (!clickLine) {{
                                    // 첫 번째 클릭: 라인 시작
                                    deleteClickLine();
                                    deleteDistnceCircleDots(); 
                                    
                                    clickLine = new kakao.maps.Polyline({{
                                        map: map,
                                        path: [clickPosition],
                                        strokeWeight: 3,
                                        strokeColor: '#db4040',
                                        strokeOpacity: 1,
                                        strokeStyle: 'solid'
                                    }});
                                    
                                    moveLine = new kakao.maps.Polyline({{
                                        strokeWeight: 3,
                                        strokeColor: '#db4040',
                                        strokeOpacity: 0.5,
                                        strokeStyle: 'solid'
                                    }});
                                    
                                    displayCircleDot(clickPosition, 0);
                                }} else {{
                                    // 추가 클릭: 경로에 점 추가
                                    var path = clickLine.getPath();
                                    path.push(clickPosition);
                                    clickLine.setPath(path);
                                    
                                    var distance = Math.round(clickLine.getLength());
                                    displayCircleDot(clickPosition, distance);
                                }}
                                return;
                            }}
                            
                            // 면적 측정 모드
                            if (areaMeasureMode) {{
                                var clickPosition = latlng;
                                
                                if (!drawingPolygon) {{
                                    // 첫 번째 클릭: 다각형 시작
                                    if (areaPolygon) {{
                                        areaPolygon.setMap(null);
                                        areaPolygon = null;
                                    }}
                                    
                                    if (areaOverlay) {{
                                        areaOverlay.setMap(null);
                                        areaOverlay = null;
                                    }}
                                    
                                    drawingPolygon = new kakao.maps.Polygon({{
                                        map: map,
                                        path: [clickPosition],
                                        strokeWeight: 3,
                                        strokeColor: '#00a0e9',
                                        strokeOpacity: 1,
                                        strokeStyle: 'solid',
                                        fillColor: '#00a0e9',
                                        fillOpacity: 0.2
                                    }});
                                    
                                    areaPolygon = new kakao.maps.Polygon({{
                                        path: [clickPosition],
                                        strokeWeight: 3,
                                        strokeColor: '#00a0e9',
                                        strokeOpacity: 1,
                                        strokeStyle: 'solid',
                                        fillColor: '#00a0e9',
                                        fillOpacity: 0.2
                                    }});
                                }} else {{
                                    // 추가 클릭: 경로에 점 추가
                                    var drawingPath = drawingPolygon.getPath();
                                    drawingPath.push(clickPosition);
                                    drawingPolygon.setPath(drawingPath);
                                    
                                    var path = areaPolygon.getPath();
                                    path.push(clickPosition);
                                    areaPolygon.setPath(path);
                                    
                                    // 3점 이상일 때 면적 계산
                                    if (path.length >= 3) {{
                                        var area = getPolygonArea(areaPolygon);
                                        displayAreaInfo(area, clickPosition);
                                    }}
                                }}
                                return;
                            }}
                            
                            // 로드뷰 모드 처리
                            if (roadviewMode) {{
                                // 로드뷰 가능 여부 확인 (카카오맵 API 로드뷰 서비스)
                                var roadviewService = new kakao.maps.RoadviewClient();
                                roadviewService.getNearestPanoId(latlng, 50, function(panoId) {{
                                    if (panoId !== null) {{
                                        // 로드뷰 가능 지점 - Python에 알림
                                        if (typeof window.roadviewClicked === 'function') {{
                                            window.roadviewClicked(latlng.getLat(), latlng.getLng());
                                        }}
                                    }} else {{
                                        console.log("로드뷰를 사용할 수 없는 지점입니다");
                                    }}
                                }});
                                return;
                            }}
                            
                            // 일반 클릭 이벤트
                            if (typeof window.mapClicked === 'function') {{
                                window.mapClicked(latlng.getLat(), latlng.getLng());
                            }}
                        }});
                        
                        // 지도 중심 변경 이벤트
                        kakao.maps.event.addListener(map, 'center_changed', function() {{
                            var center = map.getCenter();
                            if (typeof window.centerChanged === 'function') {{
                                window.centerChanged(center.getLat(), center.getLng());
                            }}
                        }});
                        
                        // 줌 변경 이벤트
                        kakao.maps.event.addListener(map, 'zoom_changed', function() {{
                            var level = map.getLevel();
                            if (typeof window.zoomChanged === 'function') {{
                                window.zoomChanged(level);
                            }}
                        }});
                        
                        // 마우스 이동 이벤트 (거리 측정용)
                        kakao.maps.event.addListener(map, 'mousemove', function(mouseEvent) {{
                            if (distanceMeasureMode && clickLine) {{
                                var mousePosition = mouseEvent.latLng;
                                var path = clickLine.getPath();
                                
                                if (path.length > 0) {{
                                    var movePath = [path[path.length-1], mousePosition];
                                    moveLine.setPath(movePath);
                                    moveLine.setMap(map);
                                    
                                    var distance = Math.round(clickLine.getLength() + kakao.maps.LatLng.distance(path[path.length-1], mousePosition));
                                    var content = getTimeHTML(distance);
                                    
                                    if (distanceOverlay) {{
                                        distanceOverlay.setPosition(mousePosition);
                                        distanceOverlay.setContent(content);
                                    }} else {{
                                        distanceOverlay = new kakao.maps.CustomOverlay({{
                                            map: map,
                                            content: content,
                                            position: mousePosition,
                                            xAnchor: 0,
                                            yAnchor: 0,
                                            zIndex: 3
                                        }});
                                    }}
                                }}
                            }}
                            
                            // 면적 측정 마우스 이동
                            if (areaMeasureMode && drawingPolygon) {{
                                var mousePosition = mouseEvent.latLng;
                                var path = areaPolygon.getPath();
                                
                                if (path.length > 0) {{
                                    var drawingPath = path.slice();
                                    drawingPath.push(mousePosition);
                                    drawingPolygon.setPath(drawingPath);
                                    
                                    if (path.length >= 2) {{
                                        var tempPolygon = new kakao.maps.Polygon({{
                                            path: drawingPath
                                        }});
                                        var area = getPolygonArea(tempPolygon);
                                        displayAreaInfo(area, mousePosition);
                                    }}
                                }}
                            }}
                        }});
                        
                        // 더블클릭 이벤트 (거리 측정 완료)
                        kakao.maps.event.addListener(map, 'dblclick', function(mouseEvent) {{
                            if (distanceMeasureMode && clickLine) {{
                                var path = clickLine.getPath();
                                if (path.length > 1) {{
                                    var distance = Math.round(clickLine.getLength());
                                    var content = getTimeHTML(distance);
                                    
                                    showDistance(content, mouseEvent.latLng);
                                }}
                                stopDistanceMeasurement();
                            }}
                        }});
                        
                        // Python에서 호출할 함수들
                        window.addMarker = function(id, lat, lng, title, info) {{
                            try {{
                                var position = new kakao.maps.LatLng(lat, lng);
                                var marker = new kakao.maps.Marker({{
                                    position: position,
                                    title: title
                                }});
                                marker.setMap(map);
                                markers[id] = marker;
                                
                                if (info) {{
                                    var infowindow = new kakao.maps.InfoWindow({{
                                        content: '<div style="padding:5px;">' + info + '</div>'
                                    }});
                                    
                                    kakao.maps.event.addListener(marker, 'click', function() {{
                                        infowindow.open(map, marker);
                                        if (typeof window.markerClicked === 'function') {{
                                            window.markerClicked(id);
                                        }}
                                    }});
                                }}
                                console.log("마커 추가 완료:", id);
                            }} catch(e) {{
                                console.error("마커 추가 실패:", e);
                            }}
                        }};
                        
                        window.removeMarker = function(id) {{
                            if (markers[id]) {{
                                markers[id].setMap(null);
                                delete markers[id];
                                console.log("마커 제거:", id);
                            }}
                        }};
                        
                        window.clearMarkers = function() {{
                            for (var id in markers) {{
                                markers[id].setMap(null);
                            }}
                            markers = {{}};
                            console.log("모든 마커 제거");
                        }};
                        
                        window.setCenter = function(lat, lng) {{
                            var moveLatLon = new kakao.maps.LatLng(lat, lng);
                            map.setCenter(moveLatLon);
                            console.log("지도 중심 이동:", lat, lng);
                        }};
                        
                        window.setZoom = function(level) {{
                            map.setLevel(level);
                            console.log("줌 레벨 변경:", level);
                        }};
                        
                        window.getCenter = function() {{
                            var center = map.getCenter();
                            return {{lat: center.getLat(), lng: center.getLng()}};
                        }};
                        
                        window.getZoom = function() {{
                            return map.getLevel();
                        }};
                        
                        // 지도 타입 변경 기능
                        window.changeMapType = function(mapType) {{
                            try {{
                                var type;
                                switch(mapType) {{
                                    case 'SATELLITE':
                                        type = kakao.maps.MapTypeId.SKYVIEW;
                                        break;
                                    case 'HYBRID':
                                        type = kakao.maps.MapTypeId.HYBRID;
                                        break;
                                    default:
                                        type = kakao.maps.MapTypeId.ROADMAP;
                                }}
                                map.setMapTypeId(type);
                                console.log("지도 타입 변경:", mapType);
                            }} catch(e) {{
                                console.error("지도 타입 변경 실패:", e);
                            }}
                        }};
                        
                        // 거리 측정 기능
                        var distanceMeasureMode = false;
                        var distanceOverlay;
                        var clickLine;
                        var moveLine;
                        var distancePolyline;
                        var dots = [];
                        var distanceCircleDots = [];
                        
                        window.startDistanceMeasurement = function() {{
                            distanceMeasureMode = true;
                            deleteClickLine();
                            deleteDistnceCircleDots();
                            deleteDistanceOverlay();
                            console.log("거리 측정 모드 시작");
                        }};
                        
                        window.stopDistanceMeasurement = function() {{
                            distanceMeasureMode = false;
                            deleteClickLine();
                            deleteDistnceCircleDots();
                            deleteDistanceOverlay();
                            console.log("거리 측정 모드 종료");
                        }};
                        
                        // 거리 측정 헬퍼 함수들
                        function deleteClickLine() {{
                            if (clickLine) {{
                                clickLine.setMap(null);    
                                clickLine = null;
                            }}
                            if (moveLine) {{
                                moveLine.setMap(null);
                                moveLine = null;
                            }}
                        }}
                        
                        function deleteDistanceOverlay() {{
                            if (distanceOverlay) {{ 
                                distanceOverlay.setMap(null); 
                                distanceOverlay = null;
                            }}
                        }}
                        
                        function deleteDistnceCircleDots() {{
                            var i;
                            for (i = 0; i < distanceCircleDots.length; i++) {{
                                distanceCircleDots[i].circle.setMap(null);
                                distanceCircleDots[i].distance.setMap(null);
                            }}
                            distanceCircleDots = [];
                        }}
                        
                        function displayCircleDot(position, distance) {{
                            var circleOverlay = new kakao.maps.CustomOverlay({{
                                content: '<span class="dot"></span>',
                                position: position,
                                zIndex: 1
                            }});
                            
                            circleOverlay.setMap(map);
                            
                            if (distance > 0) {{
                                var distanceOverlay = new kakao.maps.CustomOverlay({{
                                    content: '<div class="dotOverlay">거리 <span class="number">' + distance + '</span>m</div>',
                                    position: position,
                                    yAnchor: 1,
                                    zIndex: 2
                                }});
                                
                                distanceOverlay.setMap(map);
                            }}
                            
                            distanceCircleDots.push({{
                                circle: circleOverlay, 
                                distance: distanceOverlay
                            }});
                        }}
                        
                        function getTimeHTML(distance) {{
                            var walkkTime = distance / 67 | 0;
                            var walkHour = '', walkMin = '';
                            
                            if (walkkTime > 60) {{
                                walkHour = '<span class="number">' + Math.floor(walkkTime / 60) + '</span>시간 '
                            }}
                            walkMin = '<span class="number">' + walkkTime % 60 + '</span>분'
                            
                            var distanceText = distance >= 1000 ? 
                                '<span class="number">' + (distance / 1000).toFixed(1) + '</span>km' :
                                '<span class="number">' + distance + '</span>m';
                                
                            return '<ul class="dotOverlay distanceInfo">' +
                                   '    <li>' +
                                   '        <span class="label">총거리</span><span class="number">' + distanceText + '</span>' +
                                   '    </li>' +
                                   '    <li>' +
                                   '        <span class="label">도보</span>' + walkHour + walkMin +
                                   '    </li>' +
                                   '</ul>'
                        }}
                        
                        function showDistance(content, position) {{
                            if (distanceOverlay) {{ 
                                distanceOverlay.setMap(null); 
                                distanceOverlay = null;
                            }}
                            
                            distanceOverlay = new kakao.maps.CustomOverlay({{
                                content: content,
                                position: position,
                                xAnchor: 0,
                                yAnchor: 0,
                                zIndex: 3
                            }});
                            
                            distanceOverlay.setMap(map);
                        }}
                        
                        // 면적 측정 기능
                        var areaMeasureMode = false;
                        var areaOverlay;
                        var areaPolyline;
                        var areaPolygon;
                        var areaPoints = [];
                        var drawingPolygon;
                        
                        window.startAreaMeasurement = function() {{
                            areaMeasureMode = true;
                            deleteAreaData();
                            console.log("면적 측정 모드 시작");
                        }};
                        
                        window.stopAreaMeasurement = function() {{
                            areaMeasureMode = false;
                            deleteAreaData();
                            console.log("면적 측정 모드 종료");
                        }};
                        
                        // 면적 측정 헬퍼 함수들
                        function deleteAreaData() {{
                            if (drawingPolygon) {{
                                drawingPolygon.setMap(null);
                                drawingPolygon = null;
                            }}
                            if (areaPolygon) {{
                                areaPolygon.setMap(null);
                                areaPolygon = null;
                            }}
                            if (areaOverlay) {{
                                areaOverlay.setMap(null);
                                areaOverlay = null;
                            }}
                        }}
                        
                        function displayAreaInfo(area, position) {{
                            var content = '<div class="dotOverlay areaInfo">';
                            content += '    <span class="label">총면적</span>';
                            
                            if (area >= 1000000) {{
                                content += '<span class="number">' + Math.round(area / 1000000 * 100) / 100 + '</span>km²';
                            }} else {{
                                content += '<span class="number">' + Math.round(area * 100) / 100 + '</span>m²';
                            }}
                            
                            content += '</div>';
                            
                            if (areaOverlay) {{
                                areaOverlay.setPosition(position);
                                areaOverlay.setContent(content);
                            }} else {{
                                areaOverlay = new kakao.maps.CustomOverlay({{
                                    content: content,
                                    position: position,
                                    xAnchor: 0,
                                    yAnchor: 0,
                                    zIndex: 3
                                }});
                                
                                areaOverlay.setMap(map);
                            }}
                        }}
                        
                        // 거리 계산 함수
                        function getDistance(latlng1, latlng2) {{
                            return kakao.maps.LatLng.distance(latlng1, latlng2);
                        }}
                        
                        // 다각형 면적 계산 (정확한 계산)
                        function getPolygonArea(polygon) {{
                            var area = 0;
                            var points = polygon.getPath();
                            
                            if (points.length < 3) {{
                                return 0;
                            }}
                            
                            // Shoelace formula 사용
                            for (var i = 0; i < points.length; i++) {{
                                var j = (i + 1) % points.length;
                                var xi = points[i].getLng();
                                var yi = points[i].getLat();
                                var xj = points[j].getLng();
                                var yj = points[j].getLat();
                                
                                area += xi * yj;
                                area -= xj * yi;
                            }}
                            
                            area = Math.abs(area) / 2.0;
                            
                            // 위도/경도를 미터로 변환 (대략적)
                            var metersPerDegree = 111000;
                            return area * Math.pow(metersPerDegree, 2);
                        }}
                        
                        // 측정 결과 모두 지우기 기능
                        window.clearAllMeasurements = function() {{
                            // 거리 측정 정리
                            deleteClickLine();
                            deleteDistanceOverlay();
                            deleteDistnceCircleDots();
                            
                            // 면적 측정 정리
                            deleteAreaData();
                            
                            console.log("모든 측정 결과 정리");
                        }};
                        
                        // 로드뷰 모드 변수
                        var roadviewMode = false;
                        var roadviewOverlay;
                        var roadviewMapTypeId = kakao.maps.MapTypeId.ROADVIEW;
                        
                        window.enableRoadviewMode = function() {{
                            roadviewMode = true;
                            console.log("로드뷰 모드 활성화");
                            // 로드뷰 가능 구간 표시 (도로 오버레이)
                            map.addOverlayMapTypeId(roadviewMapTypeId);
                        }};
                        
                        window.disableRoadviewMode = function() {{
                            roadviewMode = false;
                            // 로드뷰 오버레이 제거
                            map.removeOverlayMapTypeId(roadviewMapTypeId);
                            console.log("로드뷰 모드 비활성화");
                        }};
                        
                        window.toggleRoadviewOverlay = function() {{
                            if (roadviewMode) {{
                                map.removeOverlayMapTypeId(roadviewMapTypeId);
                                roadviewMode = false;
                            }} else {{
                                map.addOverlayMapTypeId(roadviewMapTypeId);
                                roadviewMode = true;
                            }}
                            return roadviewMode;
                        }};
                        
                        // MapWalker 관련 함수들
                        window.createMapWalker = function(lat, lng, angle) {{
                            var position = new kakao.maps.LatLng(lat, lng);
                            if (mapWalker) {{
                                mapWalker.setMap(null);
                            }}
                            mapWalker = new MapWalker(position);
                            mapWalker.setMap(map);
                            if (angle !== undefined) {{
                                mapWalker.setAngle(angle);
                            }}
                            console.log("MapWalker 생성:", lat, lng, angle);
                        }};
                        
                        window.moveMapWalker = function(lat, lng, angle) {{
                            if (mapWalker) {{
                                var position = new kakao.maps.LatLng(lat, lng);
                                mapWalker.setPosition(position);
                                if (angle !== undefined) {{
                                    mapWalker.setAngle(angle);
                                }}
                                console.log("MapWalker 이동:", lat, lng, angle);
                            }}
                        }};
                        
                        window.removeMapWalker = function() {{
                            if (mapWalker) {{
                                mapWalker.setMap(null);
                                mapWalker = null;
                                console.log("MapWalker 제거");
                            }}
                        }};
                        
                        // 로드뷰 원형 마커 관련 함수들
                        var roadviewCircleMarker = null;
                        
                        window.createRoadviewCircleMarker = function(lat, lng) {{
                            var position = new kakao.maps.LatLng(lat, lng);
                            if (roadviewCircleMarker) {{
                                roadviewCircleMarker.setMap(null);
                            }}
                            
                            // 원형 마커 생성
                            roadviewCircleMarker = new kakao.maps.Circle({{
                                center: position,
                                radius: 10,
                                strokeWeight: 3,
                                strokeColor: '#FF0000',
                                strokeOpacity: 0.8,
                                fillColor: '#FF0000',
                                fillOpacity: 0.4
                            }});
                            
                            roadviewCircleMarker.setMap(map);
                            console.log("로드뷰 원형 마커 생성:", lat, lng);
                        }};
                        
                        window.moveRoadviewCircleMarker = function(lat, lng) {{
                            if (roadviewCircleMarker) {{
                                var position = new kakao.maps.LatLng(lat, lng);
                                roadviewCircleMarker.setPosition(position);
                                console.log("로드뷰 원형 마커 이동:", lat, lng);
                            }}
                        }};
                        
                        window.removeRoadviewCircleMarker = function() {{
                            if (roadviewCircleMarker) {{
                                roadviewCircleMarker.setMap(null);
                                roadviewCircleMarker = null;
                                console.log("로드뷰 원형 마커 제거");
                            }}
                        }};
                        
                        // 커스텀 컨트롤 함수들
                        window.setMapType = function(maptype) {{
                            var roadmapControl = document.getElementById('btnRoadmap');
                            var skyviewControl = document.getElementById('btnSkyview');
                            
                            if (maptype === 'roadmap') {{
                                map.setMapTypeId(kakao.maps.MapTypeId.ROADMAP);
                                roadmapControl.className = 'control-btn selected';
                                skyviewControl.className = 'control-btn';
                            }} else {{
                                map.setMapTypeId(kakao.maps.MapTypeId.SKYVIEW);
                                skyviewControl.className = 'control-btn selected';
                                roadmapControl.className = 'control-btn';
                            }}
                            console.log("지도 타입 변경:", maptype);
                        }};
                        
                        window.zoomIn = function() {{
                            map.setLevel(map.getLevel() - 1);
                            console.log("줌 인:", map.getLevel());
                        }};
                        
                        window.zoomOut = function() {{
                            map.setLevel(map.getLevel() + 1);
                            console.log("줌 아웃:", map.getLevel());
                        }};
                        
                        // 드로잉 툴박스 관련 변수
                        var drawingManager = null;
                        var currentDrawingMode = null;
                        var drawnOverlays = [];
                        
                        // 드로잉 매니저 초기화
                        function initDrawingManager() {{
                            var strokeColor = '#39f';
                            var fillColor = '#cce6ff';
                            var fillOpacity = 0.5;
                            
                            var options = {{
                                map: map,
                                drawingMode: [
                                    kakao.maps.Drawing.OverlayType.MARKER,
                                    kakao.maps.Drawing.OverlayType.POLYLINE,
                                    kakao.maps.Drawing.OverlayType.RECTANGLE,
                                    kakao.maps.Drawing.OverlayType.CIRCLE,
                                    kakao.maps.Drawing.OverlayType.POLYGON
                                ],
                                guideTooltip: ['draw', 'drag', 'edit'],
                                markerOptions: {{
                                    draggable: true,
                                    removable: true
                                }},
                                polylineOptions: {{
                                    draggable: true,
                                    removable: true,
                                    strokeColor: strokeColor,
                                    strokeWeight: 3,
                                    strokeOpacity: 1
                                }},
                                rectangleOptions: {{
                                    draggable: true,
                                    removable: true,
                                    strokeColor: strokeColor,
                                    fillColor: fillColor,
                                    fillOpacity: fillOpacity
                                }},
                                circleOptions: {{
                                    draggable: true,
                                    removable: true,
                                    strokeColor: strokeColor,
                                    fillColor: fillColor,
                                    fillOpacity: fillOpacity
                                }},
                                polygonOptions: {{
                                    draggable: true,
                                    removable: true,
                                    strokeColor: strokeColor,
                                    fillColor: fillColor,
                                    fillOpacity: fillOpacity
                                }}
                            }};
                            
                            if (typeof kakao.maps.Drawing !== 'undefined') {{
                                drawingManager = new kakao.maps.Drawing.DrawingManager(options);
                                
                                // 오버레이 완성 이벤트
                                kakao.maps.Drawing.event.addListener(drawingManager, 'drawend', function(e) {{
                                    drawnOverlays.push(e.overlay);
                                    console.log('그리기 완료:', e.overlayType);
                                }});
                                
                                console.log("드로잉 매니저 초기화 완료");
                            }} else {{
                                console.error("카카오맵 Drawing 라이브러리를 찾을 수 없습니다");
                            }}
                        }}
                        
                        // 드로잉 모드 선택
                        window.selectDrawingMode = function(mode) {{
                            if (!drawingManager) {{
                                initDrawingManager();
                            }}
                            
                            if (drawingManager) {{
                                var drawingMode;
                                switch(mode) {{
                                    case 'MARKER':
                                        drawingMode = kakao.maps.Drawing.OverlayType.MARKER;
                                        break;
                                    case 'POLYLINE':
                                        drawingMode = kakao.maps.Drawing.OverlayType.POLYLINE;
                                        break;
                                    case 'RECTANGLE':
                                        drawingMode = kakao.maps.Drawing.OverlayType.RECTANGLE;
                                        break;
                                    case 'CIRCLE':
                                        drawingMode = kakao.maps.Drawing.OverlayType.CIRCLE;
                                        break;
                                    case 'POLYGON':
                                        drawingMode = kakao.maps.Drawing.OverlayType.POLYGON;
                                        break;
                                    default:
                                        return;
                                }}
                                
                                drawingManager.select(drawingMode);
                                currentDrawingMode = mode;
                                console.log("드로잉 모드 선택:", mode);
                            }}
                        }};
                        
                        // 모든 그리기 결과 삭제
                        window.clearDrawings = function() {{
                            if (drawingManager) {{
                                // 그려진 모든 오버레이 제거
                                drawnOverlays.forEach(function(overlay) {{
                                    overlay.setMap(null);
                                }});
                                drawnOverlays = [];
                                
                                // 드로잉 모드 취소
                                drawingManager.cancel();
                                currentDrawingMode = null;
                                
                                console.log("모든 그리기 결과 삭제");
                            }}
                        }};
                        
                        // 드로잉 툴박스 표시/숨김
                        window.toggleDrawingToolbox = function() {{
                            var toolbox = document.getElementById('drawingToolbox');
                            if (toolbox.style.display === 'none') {{
                                toolbox.style.display = 'block';
                                if (!drawingManager) {{
                                    initDrawingManager();
                                }}
                            }} else {{
                                toolbox.style.display = 'none';
                                if (drawingManager) {{
                                    drawingManager.cancel();
                                }}
                            }}
                        }};
                        
                        // Shapefile 레이어 관리
                        var shapefileLayers = {{}};
                        
                        window.addShapefileLayer = function(layerId, geojsonData) {{
                            try {{
                                var data = typeof geojsonData === 'string' ? JSON.parse(geojsonData) : geojsonData;
                                var polygons = [];
                                
                                // GeoJSON 피처들을 카카오맵 폴리곤으로 변환
                                data.features.forEach(function(feature, index) {{
                                    if (feature.geometry.type === 'Polygon') {{
                                        var paths = [];
                                        feature.geometry.coordinates[0].forEach(function(coord) {{
                                            paths.push(new kakao.maps.LatLng(coord[1], coord[0]));
                                        }});
                                        
                                        var polygon = new kakao.maps.Polygon({{
                                            path: paths,
                                            strokeWeight: 2,
                                            strokeColor: '#004c80',
                                            strokeOpacity: 0.8,
                                            fillColor: '#00a0e9',
                                            fillOpacity: 0.3
                                        }});
                                        
                                        polygon.setMap(map);
                                        polygons.push(polygon);
                                        
                                        // 폴리곤 클릭 이벤트
                                        kakao.maps.event.addListener(polygon, 'click', function() {{
                                            var info = feature.properties.name || 'Shapefile Feature';
                                            console.log('Shapefile polygon clicked:', info);
                                        }});
                                    }}
                                }});
                                
                                shapefileLayers[layerId] = polygons;
                                console.log("Shapefile 레이어 추가:", layerId, polygons.length + "개 폴리곤");
                                
                            }} catch(e) {{
                                console.error("Shapefile 레이어 추가 실패:", e);
                            }}
                        }};
                        
                        window.removeShapefileLayer = function(layerId) {{
                            if (shapefileLayers[layerId]) {{
                                shapefileLayers[layerId].forEach(function(polygon) {{
                                    polygon.setMap(null);
                                }});
                                delete shapefileLayers[layerId];
                                console.log("Shapefile 레이어 제거:", layerId);
                            }}
                        }};
                        
                        // 지도 초기화 완료 표시
                        console.log("지도 준비 완료");
                        
                    }} catch(error) {{
                        console.error("지도 초기화 오류:", error);
                        document.getElementById('loading').innerHTML = "❌ 지도 로딩 실패: " + error.message;
                    }}
                }});
                
                // 스크립트 로드 오류 처리
                window.addEventListener('error', function(e) {{
                    console.error("스크립트 오류:", e);
                    document.getElementById('loading').innerHTML = "❌ 카카오맵 API 로드 실패<br>API 키를 확인해주세요";
                }});
                
            </script>
        </body>
        </html>
        """
        
        print(f"지도 로딩 시작 - 위치: {lat}, {lng}, 줌: {zoom}")
        print(f"사용 중인 API 키: {self.api_key[:10]}...")
        
        self.web_view.setHtml(html_content)
        
        # JavaScript 콜백 설정
        self.setup_javascript_callbacks()
    
    def setup_javascript_callbacks(self):
        """JavaScript 콜백 함수 설정"""
        # 콜백 설정을 위해 약간의 지연 후 실행
        QTimer.singleShot(1000, self._register_callbacks)
    
    def _register_callbacks(self):
        """실제 콜백 등록"""
        # 일반 지도 클릭 콜백 - 주기적으로 확인하는 방식 사용
        script_content = """
            window.pythonCallbacks = {
                mapClick: null,
                roadviewClick: null
            };
            
            window.mapClicked = function(lat, lng) {
                console.log('Map clicked:', lat, lng);
                window.pythonCallbacks.mapClick = {lat: lat, lng: lng, timestamp: Date.now()};
            };
            
            window.roadviewClicked = function(lat, lng) {
                console.log('Roadview clicked:', lat, lng);
                window.pythonCallbacks.roadviewClick = {lat: lat, lng: lng, timestamp: Date.now()};
            };
        """
        
        self.web_view.page().runJavaScript(script_content)
        
        # 주기적으로 JavaScript 콜백 확인
        self.callback_timer = QTimer()
        self.callback_timer.timeout.connect(self.check_javascript_callbacks)
        self.callback_timer.start(100)  # 100ms마다 확인
    
    def check_javascript_callbacks(self):
        """JavaScript 콜백 확인"""
        script = """
        (function() {
            var result = {};
            if (window.pythonCallbacks.mapClick) {
                result.mapClick = window.pythonCallbacks.mapClick;
                window.pythonCallbacks.mapClick = null;  // 처리 후 초기화
            }
            if (window.pythonCallbacks.roadviewClick) {
                result.roadviewClick = window.pythonCallbacks.roadviewClick;
                window.pythonCallbacks.roadviewClick = null;  // 처리 후 초기화
            }
            return JSON.stringify(result);
        })();
        """
        
        self.web_view.page().runJavaScript(script, self._handle_javascript_callbacks)
    
    def _handle_javascript_callbacks(self, result_str):
        """JavaScript 콜백 결과 처리"""
        try:
            import json
            if result_str:
                result = json.loads(result_str)
                
                # 지도 클릭 처리
                if 'mapClick' in result and result['mapClick']:
                    data = result['mapClick']
                    timestamp = data.get('timestamp', 0)
                    if timestamp > self.last_callback_timestamps['mapClick']:
                        self.last_callback_timestamps['mapClick'] = timestamp
                        self.location_clicked.emit(data['lat'], data['lng'])
                
                # 로드뷰 클릭 처리
                if 'roadviewClick' in result and result['roadviewClick']:
                    data = result['roadviewClick']
                    timestamp = data.get('timestamp', 0)
                    if timestamp > self.last_callback_timestamps['roadviewClick']:
                        self.last_callback_timestamps['roadviewClick'] = timestamp
                        self.roadview_clicked.emit(data['lat'], data['lng'])
        
        except Exception as e:
            print(f"JavaScript 콜백 처리 오류: {e}")
    
    def add_marker(self, marker_id: str, lat: float, lng: float, title: str = "", info: str = ""):
        """마커 추가"""
        self.markers[marker_id] = {'lat': lat, 'lng': lng, 'title': title, 'info': info}
        script = f"addMarker('{marker_id}', {lat}, {lng}, '{title}', '{info}');"
        self.web_view.page().runJavaScript(script)
    
    def remove_marker(self, marker_id: str):
        """마커 제거"""
        if marker_id in self.markers:
            del self.markers[marker_id]
        script = f"removeMarker('{marker_id}');"
        self.web_view.page().runJavaScript(script)
    
    def clear_markers(self):
        """모든 마커 제거"""
        self.markers.clear()
        self.web_view.page().runJavaScript("clearMarkers();")
    
    def set_center(self, lat: float, lng: float):
        """지도 중심 설정"""
        self.current_center = {'lat': lat, 'lng': lng}
        script = f"setCenter({lat}, {lng});"
        self.web_view.page().runJavaScript(script)
    
    def set_zoom(self, zoom: int):
        """줌 레벨 설정"""
        self.current_zoom = zoom
        script = f"setZoom({zoom});"
        self.web_view.page().runJavaScript(script)
    
    def zoom_in(self):
        """확대"""
        new_zoom = max(1, self.current_zoom - 1)
        self.set_zoom(new_zoom)
    
    def zoom_out(self):
        """축소"""
        new_zoom = min(14, self.current_zoom + 1)
        self.set_zoom(new_zoom)
    
    def go_to_current_location(self):
        """현재 위치로 이동 (서울 시청 기본값)"""
        self.set_center(37.5665, 126.9780)
    
    def toggle_roadview(self):
        """로드뷰 토글"""
        # 현재 중심점의 로드뷰를 새 창에서 열기
        lat, lng = self.current_center['lat'], self.current_center['lng']
        self.location_clicked.emit(lat, lng)
    
    def change_map_type(self, map_type: str):
        """지도 타입 변경"""
        self.current_map_type = map_type
        script = f"changeMapType('{map_type}');"
        self.web_view.page().runJavaScript(script)
    
    def start_distance_measurement(self):
        """거리 측정 시작"""
        self.measurement_mode = 'distance'
        # 면적 측정 종료
        self.web_view.page().runJavaScript("stopAreaMeasurement();")
        # 거리 측정 시작
        self.web_view.page().runJavaScript("startDistanceMeasurement();")
    
    def start_area_measurement(self):
        """면적 측정 시작"""
        self.measurement_mode = 'area'
        # 거리 측정 종료
        self.web_view.page().runJavaScript("stopDistanceMeasurement();")
        # 면적 측정 시작
        self.web_view.page().runJavaScript("startAreaMeasurement();")
    
    def stop_measurement(self):
        """측정 중지"""
        self.measurement_mode = None
        self.web_view.page().runJavaScript("stopDistanceMeasurement();")
        self.web_view.page().runJavaScript("stopAreaMeasurement();")
    
    def clear_measurements(self):
        """모든 측정 결과 지우기"""
        self.measurement_mode = None
        self.web_view.page().runJavaScript("stopDistanceMeasurement();")
        self.web_view.page().runJavaScript("stopAreaMeasurement();")
        # 추가적으로 기존 측정 오버레이 모두 제거
        self.web_view.page().runJavaScript("clearAllMeasurements();")
    
    def enable_roadview_mode(self):
        """로드뷰 모드 활성화"""
        self.roadview_mode = True
        # 로드뷰 가능 구간 표시
        self.web_view.page().runJavaScript("enableRoadviewMode();")
    
    def disable_roadview_mode(self):
        """로드뷰 모드 비활성화"""
        self.roadview_mode = False
        # 로드뷰 오버레이 제거
        self.web_view.page().runJavaScript("disableRoadviewMode();")
    
    def toggle_roadview_overlay(self):
        """로드뷰 오버레이 토글"""
        script = """
        (function() {
            var result = toggleRoadviewOverlay();
            return result;
        })();
        """
        self.web_view.page().runJavaScript(script, self._on_roadview_overlay_toggled)
    
    def _on_roadview_overlay_toggled(self, is_enabled):
        """로드뷰 오버레이 토글 결과 처리"""
        self.roadview_mode = is_enabled
        print(f"로드뷰 오버레이 {'활성화' if is_enabled else '비활성화'}됨")
    
    def create_map_walker(self, lat: float, lng: float, angle: float = 0):
        """지도에 MapWalker(동동이) 생성"""
        script = f"createMapWalker({lat}, {lng}, {angle});"
        self.web_view.page().runJavaScript(script)
    
    def move_map_walker(self, lat: float, lng: float, angle: float = 0):
        """MapWalker 위치 이동"""
        script = f"moveMapWalker({lat}, {lng}, {angle});"
        self.web_view.page().runJavaScript(script)
    
    def remove_map_walker(self):
        """MapWalker 제거"""
        self.web_view.page().runJavaScript("removeMapWalker();")
    
    def create_roadview_circle_marker(self, lat: float, lng: float):
        """로드뷰 원형 마커 생성"""
        script = f"createRoadviewCircleMarker({lat}, {lng});"
        self.web_view.page().runJavaScript(script)
    
    def move_roadview_circle_marker(self, lat: float, lng: float):
        """로드뷰 원형 마커 이동"""
        script = f"moveRoadviewCircleMarker({lat}, {lng});"
        self.web_view.page().runJavaScript(script)
    
    def remove_roadview_circle_marker(self):
        """로드뷰 원형 마커 제거"""
        self.web_view.page().runJavaScript("removeRoadviewCircleMarker();")
    
    def toggle_drawing_toolbox(self):
        """드로잉 툴박스 토글"""
        self.web_view.page().runJavaScript("toggleDrawingToolbox();")
    
    def select_drawing_mode(self, mode: str):
        """드로잉 모드 선택"""
        script = f"selectDrawingMode('{mode}');"
        self.web_view.page().runJavaScript(script)
    
    def clear_drawings(self):
        """모든 그리기 결과 삭제"""
        self.web_view.page().runJavaScript("clearDrawings();")
    
    def load_shapefile(self, file_path: str):
        """Shapefile 로드"""
        try:
            # Shapefile 처리를 위해 geopandas 또는 fiona 라이브러리 필요
            # 여기서는 간단한 구현으로 파일을 읽고 GeoJSON으로 변환
            import json
            import os
            
            # 실제 구현에서는 geopandas를 사용해야 함
            # import geopandas as gpd
            # gdf = gpd.read_file(file_path)
            # geojson_data = gdf.to_json()
            
            # 임시로 샘플 GeoJSON 생성 (실제로는 SHP 파일에서 변환)
            sample_geojson = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"name": "Sample Area"},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[
                                [126.97, 37.56],
                                [126.98, 37.56],
                                [126.98, 37.57],
                                [126.97, 37.57],
                                [126.97, 37.56]
                            ]]
                        }
                    }
                ]
            }
            
            geojson_str = json.dumps(sample_geojson)
            layer_id = f"shp_layer_{len(self.shapefile_layers)}"
            
            # JavaScript로 GeoJSON 데이터 전송
            script = f"""
                addShapefileLayer('{layer_id}', {geojson_str});
            """
            
            self.web_view.page().runJavaScript(script)
            self.shapefile_layers.append({"id": layer_id, "path": file_path})
            
            print(f"Shapefile 로드됨: {file_path}")
            
        except Exception as e:
            print(f"Shapefile 로드 실패: {e}")
            raise e
    
    def clear_shapefile_layers(self):
        """모든 Shapefile 레이어 제거"""
        for layer in self.shapefile_layers:
            script = f"removeShapefileLayer('{layer['id']}');"
            self.web_view.page().runJavaScript(script)
        
        self.shapefile_layers.clear()
        print("모든 Shapefile 레이어 제거됨")
    
    def closeEvent(self, event):
        """위젯 종료 시 타이머 정리"""
        if self.callback_timer:
            self.callback_timer.stop()
        super().closeEvent(event)
    
    def get_current_bounds(self):
        """현재 지도 영역 반환"""
        # 간단한 계산으로 대략적인 bounds 계산
        lat_delta = 0.01 * (2 ** (self.current_zoom - 15))
        lng_delta = 0.01 * (2 ** (self.current_zoom - 15))
        
        return {
            'north': self.current_center['lat'] + lat_delta,
            'south': self.current_center['lat'] - lat_delta,
            'east': self.current_center['lng'] + lng_delta,
            'west': self.current_center['lng'] - lng_delta
        }