import sys
import logging
import os
from PyQt6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont

from ui.main_window import MainWindow
from utils.config import Config
from utils.cache import Cache


def setup_logging():
    """로깅 설정"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 파일 로깅
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        filename='kakaomap_app.log',
        filemode='a',
        encoding='utf-8'
    )
    
    # 콘솔 로깅 추가
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)
    
    # 루트 로거에 콘솔 핸들러 추가
    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)
    
    logging.info("KakaoMap Clone 애플리케이션 시작")


class KakaoMapApp:
    def __init__(self):
        self.app = None
        self.main_window = None
        self.config = None
        self.cache = None
        self.splash = None
    
    def initialize(self):
        """애플리케이션 초기화"""
        logging.info("애플리케이션 초기화 시작")
        
        # WebEngine을 위한 속성 설정 (애플리케이션 생성 전에 호출)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
        
        # PyQt6 애플리케이션 생성
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("KakaoMap Clone")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("KakaoMap Clone")
        
        # 스플래시 화면 표시
        self.show_splash_screen()
        
        # 설정 초기화
        self.setup_config()
        
        # 캐시 초기화
        self.setup_cache()
        
        # 메인 윈도우 생성
        self.create_main_window()
        
        logging.info("애플리케이션 초기화 완료")
    
    def show_splash_screen(self):
        """스플래시 화면 표시"""
        try:
            # 간단한 텍스트 기반 스플래시 화면
            pixmap = QPixmap(400, 300)
            pixmap.fill(Qt.GlobalColor.white)
            
            self.splash = QSplashScreen(pixmap)
            self.splash.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
            
            # 스플래시 메시지 설정
            font = QFont("Arial", 16, QFont.Weight.Bold)
            self.splash.setFont(font)
            
            self.splash.showMessage("🗺️ KakaoMap Clone\n\n로딩 중...", 
                                  Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.black)
            self.splash.show()
            
            # 이벤트 처리로 스플래시 화면 업데이트
            self.app.processEvents()
            
        except Exception as e:
            logging.warning(f"스플래시 화면 생성 실패: {e}")
    
    def setup_config(self):
        """설정 초기화"""
        try:
            self.config = Config()
            
            if self.splash:
                self.splash.showMessage("🗺️ KakaoMap Clone\n\n설정 로딩 중...", 
                                      Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.black)
                self.app.processEvents()
            
            logging.info("설정 초기화 완료")
            
            # API 키 검증
            api_key = self.config.get_api_key('kakao_rest_api_key')
            js_api_key = self.config.get_api_key('kakao_javascript_api_key')
            
            if not api_key or api_key == 'YOUR_KAKAO_REST_API_KEY':
                logging.warning("카카오 REST API 키가 설정되지 않았습니다")
            
            if not js_api_key or js_api_key == 'YOUR_KAKAO_JAVASCRIPT_API_KEY':
                logging.warning("카카오 JavaScript API 키가 설정되지 않았습니다")
                
        except Exception as e:
            logging.error(f"설정 초기화 실패: {e}")
            self.show_error_message("설정 오류", f"설정 초기화에 실패했습니다: {e}")
    
    def setup_cache(self):
        """캐시 초기화"""
        try:
            self.cache = Cache()
            
            if self.splash:
                self.splash.showMessage("🗺️ KakaoMap Clone\n\n캐시 초기화 중...", 
                                      Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.black)
                self.app.processEvents()
            
            # 만료된 캐시 정리
            self.cache.cleanup_expired()
            
            cache_stats = self.cache.get_cache_stats()
            logging.info(f"캐시 초기화 완료 - 파일: {cache_stats['total_files']}개, "
                        f"크기: {cache_stats['total_size']} bytes")
            
        except Exception as e:
            logging.error(f"캐시 초기화 실패: {e}")
            # 캐시 초기화 실패는 치명적이지 않으므로 계속 진행
    
    def create_main_window(self):
        """메인 윈도우 생성"""
        try:
            if self.splash:
                self.splash.showMessage("🗺️ KakaoMap Clone\n\nUI 초기화 중...", 
                                      Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.black)
                self.app.processEvents()
            
            self.main_window = MainWindow(self.config)
            
            if self.splash:
                self.splash.showMessage("🗺️ KakaoMap Clone\n\n완료!", 
                                      Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.black)
                self.app.processEvents()
            
            logging.info("메인 윈도우 생성 완료")
            
        except Exception as e:
            logging.error(f"메인 윈도우 생성 실패: {e}")
            self.show_error_message("초기화 오류", f"애플리케이션 초기화에 실패했습니다: {e}")
            raise
    
    def show_error_message(self, title: str, message: str):
        """오류 메시지 표시"""
        if self.splash:
            self.splash.close()
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec()
    
    def run(self):
        """애플리케이션 실행"""
        try:
            if not self.main_window:
                logging.error("메인 윈도우가 생성되지 않았습니다")
                return 1
            
            # 스플래시 화면 숨기기 및 메인 윈도우 표시
            def show_main_window():
                if self.splash:
                    self.splash.finish(self.main_window)
                self.main_window.show()
                logging.info("메인 윈도우 표시 완료")
            
            # 약간의 지연 후 메인 윈도우 표시
            QTimer.singleShot(1000, show_main_window)
            
            # 메인 이벤트 루프 시작
            exit_code = self.app.exec()
            
            logging.info(f"애플리케이션 종료 (코드: {exit_code})")
            return exit_code
            
        except Exception as e:
            logging.error(f"애플리케이션 실행 중 오류: {e}")
            self.show_error_message("실행 오류", f"애플리케이션 실행 중 오류가 발생했습니다: {e}")
            return 1
    
    def cleanup(self):
        """애플리케이션 정리"""
        try:
            if self.cache:
                self.cache.cleanup_expired()
            
            logging.info("애플리케이션 정리 완료")
            
        except Exception as e:
            logging.error(f"애플리케이션 정리 중 오류: {e}")


def check_dependencies():
    """필수 의존성 확인"""
    required_modules = [
        'PyQt6', 'requests', 'PIL'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            if module == 'PIL':
                import PIL
            else:
                __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"다음 모듈이 설치되지 않았습니다: {', '.join(missing_modules)}")
        print("pip install -r requirements.txt 명령으로 설치해주세요.")
        return False
    
    return True


def main():
    """메인 함수"""
    try:
        # 필수 의존성 확인
        if not check_dependencies():
            return 1
        
        # 로깅 설정
        setup_logging()
        
        # 애플리케이션 인스턴스 생성 및 실행
        app_instance = KakaoMapApp()
        app_instance.initialize()
        exit_code = app_instance.run()
        
        # 정리 작업
        app_instance.cleanup()
        
        return exit_code
        
    except KeyboardInterrupt:
        logging.info("사용자에 의해 애플리케이션이 중단되었습니다")
        return 0
        
    except Exception as e:
        logging.error(f"예상치 못한 오류: {e}")
        print(f"치명적 오류: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)