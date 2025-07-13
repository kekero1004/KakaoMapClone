import requests
from typing import Dict, Any, Optional, List
from models.cctv import CCTV, CCTVArea
from utils.coordinates import Coordinates
import xml.etree.ElementTree as ET


class CCTVApi:
    def __init__(self, service_key: Optional[str] = None):
        self.service_key = service_key
        self.base_url = "https://openapi.data.go.kr"
        
        self.region_codes = {
            '11': '서울특별시',
            '26': '부산광역시',
            '27': '대구광역시',
            '28': '인천광역시',
            '29': '광주광역시',
            '30': '대전광역시',
            '31': '울산광역시',
            '36': '세종특별자치시',
            '41': '경기도',
            '42': '강원도',
            '43': '충청북도',
            '44': '충청남도',
            '45': '전라북도',
            '46': '전라남도',
            '47': '경상북도',
            '48': '경상남도',
            '50': '제주특별자치도'
        }
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[str]:
        """API 요청 수행"""
        try:
            if self.service_key:
                params['serviceKey'] = self.service_key
            
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"CCTV API 요청 실패: {e}")
            return None
    
    def _parse_xml_response(self, xml_text: str) -> List[Dict[str, Any]]:
        """XML 응답 파싱"""
        try:
            root = ET.fromstring(xml_text)
            items = []
            
            for item in root.findall('.//item'):
                item_data = {}
                for child in item:
                    item_data[child.tag] = child.text
                items.append(item_data)
            
            return items
        except ET.ParseError as e:
            print(f"XML 파싱 실패: {e}")
            return []
    
    def get_cctv_list(self, x: float, y: float, radius: float = 1.0) -> List[CCTV]:
        """주변 CCTV 목록 조회 (샘플 데이터 반환)"""
        # 네트워크 오류로 인해 API 호출 대신 샘플 데이터만 반환
        sample_cctvs = []
        
        # 서울과 부산의 샘플 데이터만 사용
        for region_code in ['11', '26']:
            cctvs = self._get_sample_cctv_data(region_code)
            sample_cctvs.extend(cctvs)
        
        nearby_cctvs = []
        for cctv in sample_cctvs:
            if cctv.x and cctv.y:
                distance = Coordinates.calculate_distance(y, x, cctv.y, cctv.x)
                if distance <= radius:
                    nearby_cctvs.append(cctv)
        
        return nearby_cctvs
    
    def get_cctv_info(self, cctv_id: str) -> Optional[CCTV]:
        """CCTV 상세 정보 조회"""
        for region_code in self.region_codes.keys():
            cctvs = self.get_cctv_by_region(region_code)
            for cctv in cctvs:
                if cctv.id == cctv_id:
                    return cctv
        return None
    
    def get_cctv_by_region(self, region_code: str) -> List[CCTV]:
        """지역별 CCTV 목록 조회 (샘플 데이터 반환)"""
        # 네트워크 연결 문제로 인해 샘플 데이터만 반환
        return self._get_sample_cctv_data(region_code)
    
    def _get_sample_cctv_data(self, region_code: str) -> List[CCTV]:
        """샘플 CCTV 데이터 (API 키가 없거나 실패시 사용)"""
        sample_data = {
            '11': [  # 서울
                {
                    'id': 'seoul_001',
                    'name': '강남역 CCTV',
                    'address': '서울특별시 강남구 강남대로 396',
                    'x': 127.027926,
                    'y': 37.498095,
                    'purpose': 'traffic',
                    'institution': '서울특별시',
                    'status': 'active'
                },
                {
                    'id': 'seoul_002', 
                    'name': '홍대입구역 CCTV',
                    'address': '서울특별시 마포구 양화로 160',
                    'x': 126.925917,
                    'y': 37.557192,
                    'purpose': 'security',
                    'institution': '서울특별시',
                    'status': 'active'
                }
            ],
            '26': [  # 부산
                {
                    'id': 'busan_001',
                    'name': '해운대해수욕장 CCTV',
                    'address': '부산광역시 해운대구 우동',
                    'x': 129.160431,
                    'y': 35.158676,
                    'purpose': 'security',
                    'institution': '부산광역시',
                    'status': 'active'
                }
            ]
        }
        
        if region_code in sample_data:
            return [CCTV.from_api_response(data) for data in sample_data[region_code]]
        return []
    
    def get_region_name(self, region_code: str) -> str:
        """지역 코드를 지역명으로 변환"""
        return self.region_codes.get(region_code, region_code)
    
    def get_all_regions(self) -> Dict[str, str]:
        """모든 지역 코드와 이름 반환"""
        return self.region_codes.copy()
    
    def create_cctv_area(self, region_code: str) -> CCTVArea:
        """지역별 CCTV 구역 생성"""
        cctvs = self.get_cctv_by_region(region_code)
        region_name = self.get_region_name(region_code)
        
        if not cctvs:
            bounds = {'north': 0, 'south': 0, 'east': 0, 'west': 0}
        else:
            lats = [cctv.y for cctv in cctvs if cctv.y]
            lngs = [cctv.x for cctv in cctvs if cctv.x]
            
            bounds = {
                'north': max(lats) if lats else 0,
                'south': min(lats) if lats else 0,
                'east': max(lngs) if lngs else 0,
                'west': min(lngs) if lngs else 0
            }
        
        return CCTVArea(name=region_name, bounds=bounds, cctv_list=cctvs)