import configparser
import os
from typing import Dict, Any, Optional


class Config:
    def __init__(self, config_file="config.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self):
        """설정 파일 로드"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file, encoding='utf-8')
        else:
            self._create_default_config()
    
    def _create_default_config(self):
        """기본 설정 파일 생성"""
        self.config['API'] = {
            'kakao_rest_api_key': 'YOUR_KAKAO_REST_API_KEY',
            'kakao_javascript_api_key': 'YOUR_KAKAO_JAVASCRIPT_API_KEY'
        }
        self.config['MAP'] = {
            'default_zoom': '15',
            'default_lat': '37.5665',
            'default_lng': '126.9780'
        }
        self.config['UI'] = {
            'window_width': '1200',
            'window_height': '800',
            'search_panel_width': '300'
        }
        self.save_config()
    
    def save_config(self):
        """설정 파일 저장"""
        with open(self.config_file, 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)
    
    def get_api_key(self, api_name: str) -> Optional[str]:
        """API 키 조회"""
        try:
            return self.config.get('API', api_name)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return None
    
    def set_api_key(self, api_name: str, api_key: str):
        """API 키 설정"""
        if 'API' not in self.config:
            self.config.add_section('API')
        self.config.set('API', api_name, api_key)
        self.save_config()
    
    def get_map_settings(self) -> Dict[str, Any]:
        """지도 설정 조회"""
        try:
            return {
                'default_zoom': self.config.getint('MAP', 'default_zoom'),
                'default_lat': self.config.getfloat('MAP', 'default_lat'),
                'default_lng': self.config.getfloat('MAP', 'default_lng')
            }
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return {
                'default_zoom': 15,
                'default_lat': 37.5665,
                'default_lng': 126.9780
            }
    
    def set_map_settings(self, **kwargs):
        """지도 설정 저장"""
        if 'MAP' not in self.config:
            self.config.add_section('MAP')
        for key, value in kwargs.items():
            self.config.set('MAP', key, str(value))
        self.save_config()
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """UI 설정 조회"""
        try:
            return {
                'window_width': self.config.getint('UI', 'window_width'),
                'window_height': self.config.getint('UI', 'window_height'),
                'search_panel_width': self.config.getint('UI', 'search_panel_width')
            }
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return {
                'window_width': 1200,
                'window_height': 800,
                'search_panel_width': 300
            }
    
    def set_ui_settings(self, **kwargs):
        """UI 설정 저장"""
        if 'UI' not in self.config:
            self.config.add_section('UI')
        for key, value in kwargs.items():
            self.config.set('UI', key, str(value))
        self.save_config()