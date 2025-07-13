import os
import pickle
import time
import hashlib
import shutil
from typing import Any, Optional


class Cache:
    def __init__(self, cache_dir="cache", default_ttl=3600):
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        self.ensure_cache_dir()
    
    def ensure_cache_dir(self):
        """캐시 디렉토리 생성"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_path(self, key: str) -> str:
        """캐시 키로부터 파일 경로 생성"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.cache")
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """캐시에 데이터 저장"""
        if ttl is None:
            ttl = self.default_ttl
        
        cache_data = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }
        
        cache_path = self._get_cache_path(key)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
        except Exception as e:
            print(f"캐시 저장 실패: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            if time.time() > cache_data['expires_at']:
                self.delete(key)
                return None
            
            return cache_data['value']
        except Exception as e:
            print(f"캐시 로드 실패: {e}")
            self.delete(key)
            return None
    
    def delete(self, key: str):
        """캐시에서 데이터 삭제"""
        cache_path = self._get_cache_path(key)
        try:
            if os.path.exists(cache_path):
                os.remove(cache_path)
        except Exception as e:
            print(f"캐시 삭제 실패: {e}")
    
    def clear(self):
        """모든 캐시 데이터 삭제"""
        try:
            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                self.ensure_cache_dir()
        except Exception as e:
            print(f"캐시 전체 삭제 실패: {e}")
    
    def is_expired(self, cache_file: str) -> bool:
        """캐시 만료 여부 확인"""
        try:
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            return time.time() > cache_data['expires_at']
        except Exception:
            return True
    
    def cleanup_expired(self):
        """만료된 캐시 정리"""
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    cache_path = os.path.join(self.cache_dir, filename)
                    if self.is_expired(cache_path):
                        os.remove(cache_path)
        except Exception as e:
            print(f"만료된 캐시 정리 실패: {e}")
    
    def get_cache_size(self) -> int:
        """캐시 크기 조회 (바이트 단위)"""
        total_size = 0
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    cache_path = os.path.join(self.cache_dir, filename)
                    total_size += os.path.getsize(cache_path)
        except Exception as e:
            print(f"캐시 크기 계산 실패: {e}")
        return total_size
    
    def get_cache_stats(self) -> dict:
        """캐시 통계 정보 조회"""
        stats = {
            'total_files': 0,
            'total_size': 0,
            'expired_files': 0
        }
        
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    cache_path = os.path.join(self.cache_dir, filename)
                    stats['total_files'] += 1
                    stats['total_size'] += os.path.getsize(cache_path)
                    
                    if self.is_expired(cache_path):
                        stats['expired_files'] += 1
        except Exception as e:
            print(f"캐시 통계 계산 실패: {e}")
        
        return stats