# YouTube Shorts Automation Backend

YouTube Shorts 자동 생성을 위한 FastAPI 백엔드 서비스입니다.

## 기능

- 사용자 설명을 바탕으로 10개의 이미지 프롬프트 자동 생성 (OpenAI GPT-4)
- Krea AI를 통한 이미지 자동 생성
- Minimax API를 통한 비디오 생성
- 프로젝트 관리 및 파일 저장
- 이미지 수동 업데이트 기능

## 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env.example`을 복사하여 `.env` 파일을 생성하고 API 키를 설정하세요:

```bash
cp .env.example .env
```

`.env` 파일에 다음 정보를 입력:

```
OPENAI_API_KEY=your_openai_api_key
KREA_EMAIL=your_krea_email
KREA_PASSWORD=your_krea_password
MINIMAX_API_KEY=your_minimax_api_key
```

### 3. 서버 실행

```bash
python main.py
```

또는

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API 엔드포인트

### 프로젝트 생성

```
POST /api/projects/create
```

요청 본문:

```json
{
  "description": "고양이가 우주를 여행하는 이야기"
}
```

### 이미지 생성

```
POST /api/projects/{project_id}/generate-images
```

### 비디오 생성

```
POST /api/projects/{project_id}/generate-videos
```

### 프로젝트 조회

```
GET /api/projects/{project_id}
```

### 모든 프로젝트 목록

```
GET /api/projects
```

### 이미지 업데이트

```
PUT /api/projects/{project_id}/images/{image_index}
```

### 파일 서빙

```
GET /files/{project_id}/{filename}
```

## 프로젝트 구조

```
shortsTubeBackend/
├── main.py                 # FastAPI 메인 애플리케이션
├── requirements.txt        # Python 의존성
├── .env.example           # 환경 변수 템플릿
├── services/              # 서비스 모듈들
│   ├── __init__.py
│   ├── openai_service.py  # OpenAI API 서비스
│   ├── krea_automation.py # Krea 웹 자동화
│   ├── minimax_service.py # Minimax 비디오 생성
│   └── file_manager.py    # 파일 관리
├── downloads/             # 생성된 파일들
│   ├── krea_images/      # Krea에서 생성된 이미지
│   └── videos/           # 생성된 비디오
└── projects/             # 프로젝트 데이터
    └── {project_id}/
        ├── project.json  # 프로젝트 메타데이터
        └── images/       # 업로드된 이미지
```

## 개발 노트

### MVP 구현 상태

현재는 MVP(Minimum Viable Product) 버전으로, 다음과 같은 더미 구현이 포함되어 있습니다:

1. **Krea 자동화**: 실제 웹 자동화 대신 placeholder 이미지 사용
2. **Minimax 비디오 생성**: 실제 API 호출 대신 더미 파일 생성
3. **이미지 선택**: GPT-4 Vision 대신 첫 번째 이미지 자동 선택

### 실제 구현을 위한 TODO

1. Krea 웹사이트의 실제 DOM 구조에 맞춰 Selenium 자동화 구현
2. Minimax API 실제 연동
3. GPT-4 Vision API를 사용한 이미지 품질 평가 및 선택
4. 에러 처리 및 로깅 개선
5. 데이터베이스 연동 (현재는 파일 시스템 사용)

## 라이선스

MIT License
