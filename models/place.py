from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Place:
    id: str
    name: str
    address: str
    road_address: str
    x: float
    y: float
    category: str
    phone: str
    url: str
    distance: Optional[float] = None
    
    @classmethod
    def from_kakao_response(cls, data: Dict[str, Any]) -> 'Place':
        """카카오 API 응답으로부터 Place 객체 생성"""
        return cls(
            id=data.get('id', ''),
            name=data.get('place_name', ''),
            address=data.get('address_name', ''),
            road_address=data.get('road_address_name', ''),
            x=float(data.get('x', 0)),
            y=float(data.get('y', 0)),
            category=data.get('category_name', ''),
            phone=data.get('phone', ''),
            url=data.get('place_url', ''),
            distance=float(data.get('distance', 0)) if data.get('distance') else None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Place 객체를 딕셔너리로 변환"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'road_address': self.road_address,
            'x': self.x,
            'y': self.y,
            'category': self.category,
            'phone': self.phone,
            'url': self.url,
            'distance': self.distance
        }
    
    def get_display_address(self) -> str:
        """표시용 주소 반환 (도로명 주소 우선)"""
        return self.road_address if self.road_address else self.address
    
    def has_phone(self) -> bool:
        """전화번호 존재 여부"""
        return bool(self.phone and self.phone.strip())
    
    def get_short_category(self) -> str:
        """축약된 카테고리명 반환"""
        if not self.category:
            return ''
        
        parts = self.category.split(' > ')
        return parts[-1] if parts else self.category