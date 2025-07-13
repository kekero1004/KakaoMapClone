import requests
from typing import Dict, Any, Optional, List
import json


class KakaoMapAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://dapi.kakao.com"
        self.headers = {
            "Authorization": f"KakaoAK {api_key}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """API 요청 수행"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API 요청 실패: {e}")
            return None
    
    def search_keyword(self, query: str, x: Optional[float] = None, y: Optional[float] = None, 
                      radius: Optional[int] = None, page: int = 1, size: int = 15) -> Optional[Dict[str, Any]]:
        """키워드 검색"""
        params = {
            "query": query,
            "page": page,
            "size": size
        }
        
        if x is not None and y is not None:
            params["x"] = x
            params["y"] = y
            
        if radius is not None:
            params["radius"] = radius
            
        return self._make_request("/v2/local/search/keyword.json", params)
    
    def search_address(self, query: str) -> Optional[Dict[str, Any]]:
        """주소 검색"""
        params = {"query": query}
        return self._make_request("/v2/local/search/address.json", params)
    
    def coord_to_address(self, x: float, y: float) -> Optional[Dict[str, Any]]:
        """좌표를 주소로 변환 (역지오코딩)"""
        params = {
            "x": x,
            "y": y
        }
        return self._make_request("/v2/local/geo/coord2address.json", params)
    
    def coord_to_region(self, x: float, y: float) -> Optional[Dict[str, Any]]:
        """좌표를 행정구역 정보로 변환"""
        params = {
            "x": x,
            "y": y
        }
        return self._make_request("/v2/local/geo/coord2regioncode.json", params)
    
    def get_roadview(self, x: float, y: float, level: int = 1, 
                    width: int = 640, height: int = 360) -> Optional[str]:
        """로드뷰 이미지 URL 생성"""
        roadview_url = "https://map.kakaoapi.com/roadview"
        params = {
            "level": level,
            "width": width,
            "height": height,
            "x": x,
            "y": y
        }
        
        return f"{roadview_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
    
    def check_roadview_available(self, x: float, y: float) -> bool:
        """로드뷰 이용 가능 여부 확인"""
        try:
            roadview_info_url = "https://dapi.kakao.com/v2/local/geo/coord2roadview.json"
            params = {"x": x, "y": y}
            response = requests.get(roadview_info_url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return len(data.get('documents', [])) > 0
            return False
        except Exception:
            return False
    
    def search_category(self, category_group_code: str, x: Optional[float] = None, 
                       y: Optional[float] = None, radius: Optional[int] = None,
                       page: int = 1, size: int = 15) -> Optional[Dict[str, Any]]:
        """카테고리 검색"""
        params = {
            "category_group_code": category_group_code,
            "page": page,
            "size": size
        }
        
        if x is not None and y is not None:
            params["x"] = x
            params["y"] = y
            
        if radius is not None:
            params["radius"] = radius
            
        return self._make_request("/v2/local/search/category.json", params)