from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class CCTV:
    id: str
    name: str
    address: str
    x: float
    y: float
    purpose: str
    institution: str
    status: str
    installation_date: Optional[str] = None
    pixel_count: Optional[str] = None
    manage_agency: Optional[str] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'CCTV':
        """공공 API 응답으로부터 CCTV 객체 생성"""
        return cls(
            id=str(data.get('cctvId', data.get('id', ''))),
            name=data.get('cctvName', data.get('name', '')),
            address=data.get('address', data.get('cctvAddress', '')),
            x=float(data.get('longitude', data.get('x', 0))),
            y=float(data.get('latitude', data.get('y', 0))),
            purpose=data.get('purpose', data.get('cctvPurpose', '')),
            institution=data.get('institution', data.get('cctvInstitution', '')),
            status=data.get('status', data.get('cctvStatus', 'unknown')),
            installation_date=data.get('installationDate', data.get('cctvInstallDate')),
            pixel_count=data.get('pixelCount', data.get('cctvPixel')),
            manage_agency=data.get('manageAgency', data.get('cctvManageAgency'))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """CCTV 객체를 딕셔너리로 변환"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'x': self.x,
            'y': self.y,
            'purpose': self.purpose,
            'institution': self.institution,
            'status': self.status,
            'installation_date': self.installation_date,
            'pixel_count': self.pixel_count,
            'manage_agency': self.manage_agency
        }
    
    def is_active(self) -> bool:
        """CCTV 활성 상태 확인"""
        return self.status.lower() in ['active', 'normal', '정상', '운영중']
    
    def get_display_name(self) -> str:
        """표시용 이름 반환"""
        if self.name:
            return self.name
        return f"CCTV {self.id}"
    
    def get_purpose_korean(self) -> str:
        """목적을 한국어로 반환"""
        purpose_map = {
            'traffic': '교통',
            'security': '보안',
            'crime_prevention': '방범',
            'disaster': '재해',
            'fire': '화재',
            'general': '일반'
        }
        return purpose_map.get(self.purpose.lower(), self.purpose)
    
    def get_coordinates(self) -> tuple:
        """좌표를 튜플로 반환"""
        return (self.y, self.x)


@dataclass 
class CCTVArea:
    """CCTV 구역 정보"""
    name: str
    bounds: Dict[str, float]
    cctv_list: List[CCTV]
    
    def get_cctv_count(self) -> int:
        """구역 내 CCTV 개수"""
        return len(self.cctv_list)
    
    def get_active_cctv_count(self) -> int:
        """구역 내 활성 CCTV 개수"""
        return sum(1 for cctv in self.cctv_list if cctv.is_active())
    
    def get_cctv_by_purpose(self, purpose: str) -> List[CCTV]:
        """목적별 CCTV 필터링"""
        return [cctv for cctv in self.cctv_list if cctv.purpose.lower() == purpose.lower()]