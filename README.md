# 🗺️ KakaoMap Clone

Python PyQt6과 카카오맵 API를 이용한 데스크톱 지도 애플리케이션

<img width="1695" height="995" alt="image" src="https://github.com/user-attachments/assets/305aa04c-c6e6-4d32-9526-bcc4b1b60df4" />

## ✨ 주요 기능

- 📍 **지도 검색 및 탐색**: 키워드 및 카테고리별 장소 검색
- 👁️ **로드뷰 기능**: 360도 파노라마 이미지 뷰어
- 📹 **CCTV 정보**: 공공 CCTV 위치 및 정보 표시
- 🔍 **지오코딩**: 주소 ↔ 좌표 변환
- 💾 **캐싱 시스템**: 효율적인 데이터 관리
- ⚙️ **설정 관리**: 사용자 맞춤 설정

## 🛠️ 기술 스택

- **언어**: Python 3.12
- **GUI**: PyQt6
- **API**: Kakao Map API, Kakao Local API
- **기타**: requests, Pillow

## 📦 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd 00_KAKAOMAPCLONE
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. API 키 설정
`config.ini` 파일에서 카카오 API 키를 설정:

```ini
[API]
kakao_rest_api_key = YOUR_KAKAO_REST_API_KEY
kakao_javascript_api_key = YOUR_KAKAO_JAVASCRIPT_API_KEY
```

### 4. 애플리케이션 실행

#### Windows
```batch
run.bat
```

#### Linux/Mac
```bash
./run.sh
```

#### 직접 실행
```bash
python main.py
```

## 📁 완전한 프로젝트 구조

### 루트 디렉토리 구조
```
D:\00_KAKAOMAPCLONE\
├── 📄 README.md                    # 프로젝트 메인 문서 (이 파일)
├── 📋 dev.md                       # 개발 계획서 및 상세 명세
├── ⚙️ config.ini                   # 설정 파일 (API 키, 기본값)
├── 📦 requirements.txt             # Python 의존성 패키지 목록
├── 🚀 main.py                      # 메인 애플리케이션 진입점
├── 🖥️ run.bat                     # Windows 실행 스크립트
├── 🐧 run.sh                      # Linux/Mac 실행 스크립트
├── 🌐 api\                        # API 통신 레이어
├── 🏗️ models\                     # 데이터 모델 정의
├── 🖼️ ui\                         # 사용자 인터페이스 컴포넌트
├── 🛠️ utils\                      # 공용 유틸리티 함수
└── 📂 resources\                   # 정적 리소스 파일
```

### API 레이어 (`api/`)
```
api\
├── 📁 __init__.py                  # 패키지 초기화 파일
├── 🗺️ kakao_map_api.py           # 카카오맵 API 클라이언트
│   ├── 🔍 키워드/주소 검색
│   ├── 📍 좌표 ↔ 주소 변환 (지오코딩)
│   ├── 👁️ 로드뷰 이미지 URL 생성
│   ├── 🏷️ 카테고리별 장소 검색
│   └── ✅ 로드뷰 이용 가능 여부 확인
├── 📍 kakao_local_api.py          # 카카오 로컬 검색 API
│   ├── 🔎 키워드 기반 장소 검색
│   ├── 🏷️ 카테고리 코드 기반 검색
│   ├── 📄 페이지네이션 지원
│   └── 📊 19개 주요 카테고리 지원
└── 📹 cctv_api.py                 # 공공 CCTV 데이터 API
    ├── 🌍 전국 17개 시도별 CCTV 조회
    ├── 📍 주변 CCTV 검색 (반경 기반)
    ├── 🔍 CCTV 상세 정보 조회
    └── 🎯 샘플 데이터 제공 (API 키 없을 시)
```

### 데이터 모델 (`models/`)
```
models\
├── 📁 __init__.py                  # 패키지 초기화 파일
├── 📍 place.py                    # 장소 정보 데이터 모델
│   ├── 🏢 Place 클래스 (장소 기본 정보)
│   ├── 🔄 카카오 API 응답 파싱
│   ├── 📱 표시용 주소/카테고리 변환
│   └── 📞 전화번호 유효성 검사
└── 📹 cctv.py                     # CCTV 정보 데이터 모델
    ├── 📹 CCTV 클래스 (CCTV 기본 정보)
    ├── 🏘️ CCTVArea 클래스 (구역별 관리)
    ├── 🎯 목적별 분류 (교통/보안/방범 등)
    └── ✅ 활성 상태 확인 기능
```

### 사용자 인터페이스 (`ui/`)
```
ui\
├── 📁 __init__.py                  # 패키지 초기화 파일
├── 🏠 main_window.py              # 메인 애플리케이션 윈도우
│   ├── 📋 메뉴바 (파일/보기/도구/도움말)
│   ├── 🔧 툴바 (현재위치/CCTV/로드뷰)
│   ├── 📊 상태바 (진행상황/좌표 표시)
│   ├── 🧵 백그라운드 검색 워커
│   └── 📱 전체 레이아웃 관리
├── 🗺️ map_widget.py              # 지도 표시 위젯
│   ├── 🌐 카카오맵 JavaScript API 통합
│   ├── 📍 마커 추가/제거/관리
│   ├── 🔍 줌 인/아웃 컨트롤
│   ├── 🖱️ 지도 드래그 이동
│   └── 📍 클릭 좌표 이벤트 처리
├── 🔍 search_widget.py           # 검색 인터페이스 위젯
│   ├── 🔎 검색어 입력 필드
│   ├── 🏷️ 카테고리 필터 (19개 카테고리)
│   ├── 📋 검색 결과 리스트 (스크롤 가능)
│   ├── ➕ 더보기 기능 (페이지네이션)
│   └── 🎨 커스텀 결과 아이템 디자인
└── 👁️ roadview_widget.py         # 로드뷰 표시 위젯
    ├── 🖼️ 360도 파노라마 이미지 표시
    ├── 🎮 방향 컨트롤 (상하좌우 버튼)
    ├── 🔍 줌 컨트롤 (확대/축소)
    ├── 🎚️ 슬라이더 조정 (팬/틸트)
    ├── 🔄 새로고침 기능
    └── ❌ 닫기 버튼
```

### 유틸리티 (`utils/`)
```
utils\
├── 📁 __init__.py                  # 패키지 초기화 파일
├── ⚙️ config.py                   # 설정 파일 관리
│   ├── 📝 config.ini 읽기/쓰기
│   ├── 🔑 API 키 관리
│   ├── 🗺️ 지도 기본 설정
│   ├── 🖥️ UI 설정 (창 크기 등)
│   └── 🛡️ 안전한 설정 파일 처리
├── 📐 coordinates.py              # 좌표 변환 유틸리티
│   ├── 🌍 WGS84 ↔ GRS80 좌표계 변환
│   ├── 📏 하버사인 공식 거리 계산
│   ├── 🧭 방위각 계산
│   ├── 📦 경계 좌표 계산
│   ├── 🔢 픽셀당 미터 계산
│   └── 🗺️ 타일 좌표 변환
└── 💾 cache.py                    # 데이터 캐싱 시스템
    ├── 🗃️ 파일 기반 캐시 저장
    ├── ⏰ TTL (Time To Live) 지원
    ├── 🧹 만료된 캐시 자동 정리
    ├── 📊 캐시 통계 정보
    └── 🔐 MD5 해시 기반 키 생성
```

### 리소스 (`resources/`)
```
resources\
├── 🎨 icons\                      # 아이콘 파일 디렉토리 (현재 비어있음)
│   └── (향후 앱 아이콘, UI 아이콘 저장 예정)
└── 🎨 styles\                     # 스타일시트 디렉토리 (현재 비어있음)
    └── (향후 CSS, QSS 스타일 파일 저장 예정)
```

### 설정 및 실행 파일
```
📄 config.ini                      # 애플리케이션 설정
├── [API] 섹션
│   ├── kakao_rest_api_key         # 카카오 REST API 키
│   └── kakao_javascript_api_key   # 카카오 JavaScript API 키
├── [MAP] 섹션
│   ├── default_zoom = 15          # 기본 줌 레벨
│   ├── default_lat = 37.5665      # 기본 위도 (서울시청)
│   └── default_lng = 126.9780     # 기본 경도 (서울시청)
└── [UI] 섹션
    ├── window_width = 1200        # 창 너비
    ├── window_height = 800        # 창 높이
    └── search_panel_width = 300   # 검색 패널 너비

📦 requirements.txt                # Python 의존성
├── PyQt6>=6.6.0                  # GUI 프레임워크
├── requests>=2.31.0              # HTTP 클라이언트
└── Pillow>=10.0.0                # 이미지 처리

🖥️ run.bat                        # Windows 실행 스크립트
├── Python 설치 확인
├── 의존성 자동 설치
├── 애플리케이션 실행
└── 오류 처리

🐧 run.sh                         # Linux/Mac 실행 스크립트
├── Python3 설치 확인
├── 의존성 자동 설치
├── 애플리케이션 실행
└── 오류 처리
```

## 📊 프로젝트 통계

### 파일 개수 및 구성
```
📊 전체 프로젝트 구성
├── 📁 총 디렉토리: 6개
├── 📄 총 파일: 20개
├── 🐍 Python 파일: 13개
├── ⚙️ 설정 파일: 3개 (config.ini, requirements.txt, dev.md)
├── 📋 문서 파일: 2개 (README.md, dev.md)
└── 🚀 실행 스크립트: 2개 (run.bat, run.sh)

📈 코드 라인 분석 (추정)
├── 🗺️ 지도 관련: ~800 라인
├── 🔍 검색 기능: ~600 라인
├── 👁️ 로드뷰: ~400 라인
├── 📹 CCTV 기능: ~300 라인
├── 🛠️ 유틸리티: ~500 라인
└── 📱 UI 통합: ~700 라인
총 코드 라인: ~3,300 라인 (추정)
```

## 🎯 사용법

### 기본 조작
1. **검색**: 왼쪽 패널에서 장소나 주소 검색
2. **지도 이동**: 마우스 드래그로 지도 이동
3. **줌**: 마우스 휠 또는 버튼으로 확대/축소
4. **로드뷰**: 지도 클릭 또는 로드뷰 버튼으로 활성화

### 주요 기능
- **카테고리 검색**: 음식점, 카페, 병원 등 카테고리별 검색
- **CCTV 표시**: 툴바의 CCTV 버튼으로 주변 CCTV 표시
- **패널 토글**: 보기 메뉴에서 검색/로드뷰 패널 숨기기/표시

### 키보드 단축키
- **Ctrl+Q**: 애플리케이션 종료
- **F5**: 현재 위치로 이동
- **Ctrl+F**: 검색 입력 필드 포커스

## ⚙️ 설정

### config.ini 파일 구조
```ini
[API]
kakao_rest_api_key = YOUR_API_KEY
kakao_javascript_api_key = YOUR_API_KEY

[MAP]
default_zoom = 15
default_lat = 37.5665
default_lng = 126.9780

[UI]
window_width = 1200
window_height = 800
search_panel_width = 300
```

## 🔧 개발

### MVC 아키텍처
- **Model**: `models/` - 데이터 구조 및 비즈니스 로직
- **View**: `ui/` - 사용자 인터페이스 컴포넌트
- **Controller**: `api/` - API 통신 및 데이터 처리

### 확장성
- 새로운 API 추가: `api/` 디렉토리에 API 클래스 추가
- UI 컴포넌트 추가: `ui/` 디렉토리에 위젯 클래스 추가
- 데이터 모델 추가: `models/` 디렉토리에 모델 클래스 추가

### 개발 환경 설정
```bash
# 개발 모드로 실행 (디버그 로그 활성화)
python main.py --debug

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 개발 의존성 설치
pip install -r requirements.txt
pip install pytest black flake8  # 개발 도구
```

## 📝 로그 및 디버깅

### 로그 파일
- **애플리케이션 로그**: `kakaomap_app.log`
- **캐시 통계**: 도구 > 캐시 정리에서 확인 가능
- **콘솔 출력**: 터미널에서 실시간 로그 확인

### 디버그 모드
```bash
# 디버그 로그와 함께 실행
python main.py --verbose

# 개발자 도구 활성화
python -c "
import sys
sys.argv.append('--debug')
exec(open('main.py').read())
"
```

## 🔧 성능 최적화

### 캐시 시스템
- **이미지 캐시**: 로드뷰 이미지 자동 캐싱 (1시간 TTL)
- **검색 결과 캐시**: API 응답 캐싱으로 중복 요청 방지
- **좌표 변환 캐시**: 자주 사용하는 좌표 변환 결과 저장

### 메모리 관리
- **백그라운드 스레드**: 검색 작업을 메인 UI와 분리
- **이미지 압축**: 로드뷰 이미지 자동 리사이징
- **마커 관리**: 화면 밖 마커 자동 정리

## ⚠️ 주의사항

1. **API 키**: 카카오 개발자 센터에서 발급받은 유효한 API 키 필요
2. **네트워크**: 인터넷 연결 필요 (지도 타일, API 호출)
3. **브라우저 엔진**: PyQt6 WebEngine 필요
4. **방화벽**: 카카오 API 도메인에 대한 HTTPS 통신 허용 필요

## 🐛 문제 해결

### 자주 발생하는 문제

#### 1. API 키 관련
```
문제: "API 키가 필요합니다" 오류
해결: config.ini에서 올바른 API 키 설정 확인
```

#### 2. 의존성 문제
```
문제: "ModuleNotFoundError: No module named 'PyQt6'"
해결: pip install -r requirements.txt 실행
```

#### 3. 지도 로딩 실패
```
문제: 지도가 표시되지 않음
해결: 
- 인터넷 연결 확인
- 방화벽 설정 확인  
- JavaScript API 키 확인
```

#### 4. 로드뷰 오류
```
문제: 로드뷰 이미지가 로드되지 않음
해결:
- 해당 위치의 로드뷰 제공 여부 확인
- REST API 키 확인
- 네트워크 연결 상태 확인
```

### 로그 분석
```bash
# 오류 로그 확인
tail -f kakaomap_app.log | grep ERROR

# 특정 기능 로그 확인
grep "검색" kakaomap_app.log
grep "로드뷰" kakaomap_app.log
```

## 📄 라이선스

이 프로젝트는 교육 목적으로 작성되었습니다.
카카오맵 API 이용약관을 준수해야 합니다.

## 🤝 기여

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 지원

문제가 발생하면 Issue를 생성해주세요.

---

**KakaoMap Clone** - Python & PyQt6로 만든 지도 애플리케이션 🗺️
