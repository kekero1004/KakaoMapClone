import requests
from typing import Dict, Any, Optional, List
from models.place import Place


class KakaoLocalAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://dapi.kakao.com"
        self.headers = {
            "Authorization": f"KakaoAK {api_key}",
            "Content-Type": "application/json"
        }
        
        self.category_codes = {
            'MT1': '대형마트',
            'CS2': '편의점', 
            'PS3': '어린이집, 유치원',
            'SC4': '학교',
            'AC5': '학원',
            'PK6': '주차장',
            'OL7': '주유소, 충전소',
            'SW8': '지하철역',
            'BK9': '은행',
            'CT1': '문화시설',
            'AG2': '중개업소',
            'PO3': '공공기관',
            'AT4': '관광명소',
            'AD5': '숙박',
            'FD6': '음식점',
            'CE7': '카페',
            'HP8': '병원',
            'PM9': '약국'
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
    
    def search_by_keyword(self, query: str, x: Optional[float] = None, y: Optional[float] = None, 
                         radius: Optional[int] = None, page: int = 1, size: int = 15) -> List[Place]:
        """키워드로 장소 검색"""
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
            
        response = self._make_request("/v2/local/search/keyword.json", params)
        
        if response and 'documents' in response:
            return [Place.from_kakao_response(doc) for doc in response['documents']]
        return []
    
    def search_by_category(self, category_group_code: str, x: Optional[float] = None, 
                          y: Optional[float] = None, radius: Optional[int] = None,
                          page: int = 1, size: int = 15) -> List[Place]:
        """카테고리로 장소 검색"""
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
            
        response = self._make_request("/v2/local/search/category.json", params)
        
        if response and 'documents' in response:
            return [Place.from_kakao_response(doc) for doc in response['documents']]
        return []
    
    def get_place_detail(self, place_id: str) -> Optional[Place]:
        """장소 상세 정보 조회 (ID로 검색)"""
        params = {"query": place_id}
        response = self._make_request("/v2/local/search/keyword.json", params)
        
        if response and 'documents' in response and response['documents']:
            return Place.from_kakao_response(response['documents'][0])
        return None
    
    def search_nearby_places(self, x: float, y: float, radius: int = 1000, 
                           category: Optional[str] = None) -> List[Place]:
        """주변 장소 검색"""
        if category and category in self.category_codes:
            return self.search_by_category(category, x, y, radius)
        else:
            return self.search_by_keyword("", x, y, radius)
    
    def get_category_name(self, category_code: str) -> str:
        """카테고리 코드를 한글명으로 변환"""
        return self.category_codes.get(category_code, category_code)
    
    def get_all_categories(self) -> Dict[str, str]:
        """모든 카테고리 코드와 이름 반환"""
        return self.category_codes.copy()
    
    def search_with_pagination(self, query: str, total_pages: int = 3, 
                             **kwargs) -> List[Place]:
        """페이지네이션을 통한 확장 검색"""
        all_places = []
        
        for page in range(1, total_pages + 1):
            places = self.search_by_keyword(query, page=page, **kwargs)
            if not places:
                break
            all_places.extend(places)
            
        return all_places