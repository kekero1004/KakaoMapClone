import math
from typing import Tuple, Dict


class Coordinates:
    EARTH_RADIUS_KM = 6371.0
    
    @staticmethod
    def wgs84_to_grs80(lat: float, lng: float) -> Tuple[float, float]:
        """WGS84 좌표계를 GRS80으로 변환"""
        delta_lat = 0.00010576
        delta_lng = 0.00011059
        
        grs80_lat = lat - delta_lat
        grs80_lng = lng - delta_lng
        
        return grs80_lat, grs80_lng
    
    @staticmethod
    def grs80_to_wgs84(x: float, y: float) -> Tuple[float, float]:
        """GRS80 좌표계를 WGS84로 변환"""
        delta_lat = 0.00010576
        delta_lng = 0.00011059
        
        wgs84_lat = x + delta_lat
        wgs84_lng = y + delta_lng
        
        return wgs84_lat, wgs84_lng
    
    @staticmethod
    def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """두 좌표 간의 거리 계산 (하버사인 공식) - km 단위"""
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        dlat = lat2_rad - lat1_rad
        dlng = lng2_rad - lng1_rad
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        return Coordinates.EARTH_RADIUS_KM * c
    
    @staticmethod
    def calculate_bearing(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """두 좌표 간의 방위각 계산 (도 단위)"""
        lat1_rad = math.radians(lat1)
        lng1_rad = math.radians(lng1)
        lat2_rad = math.radians(lat2)
        lng2_rad = math.radians(lng2)
        
        dlng = lng2_rad - lng1_rad
        
        y = math.sin(dlng) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlng))
        
        bearing = math.atan2(y, x)
        bearing_degrees = math.degrees(bearing)
        
        return (bearing_degrees + 360) % 360
    
    @staticmethod
    def get_bounds(center_lat: float, center_lng: float, radius_km: float) -> Dict[str, float]:
        """중심점과 반경으로 경계 좌표 계산"""
        lat_delta = radius_km / 111.0
        lng_delta = radius_km / (111.0 * math.cos(math.radians(center_lat)))
        
        return {
            'north': center_lat + lat_delta,
            'south': center_lat - lat_delta,
            'east': center_lng + lng_delta,
            'west': center_lng - lng_delta
        }
    
    @staticmethod
    def is_within_bounds(lat: float, lng: float, bounds: Dict[str, float]) -> bool:
        """좌표가 경계 내에 있는지 확인"""
        return (bounds['south'] <= lat <= bounds['north'] and
                bounds['west'] <= lng <= bounds['east'])
    
    @staticmethod
    def meters_per_pixel(lat: float, zoom: int) -> float:
        """주어진 위도와 줌 레벨에서 픽셀당 미터 계산"""
        return 156543.03392 * math.cos(math.radians(lat)) / (2 ** zoom)
    
    @staticmethod
    def tile_to_latlon(x: int, y: int, zoom: int) -> Tuple[float, float]:
        """타일 좌표를 위경도로 변환"""
        n = 2.0 ** zoom
        lon_deg = x / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
        lat_deg = math.degrees(lat_rad)
        return lat_deg, lon_deg
    
    @staticmethod
    def latlon_to_tile(lat: float, lng: float, zoom: int) -> Tuple[int, int]:
        """위경도를 타일 좌표로 변환"""
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        x = int((lng + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return x, y