# YouTube Shorts 자동화 시스템

OpenAI GPT-4.1 + Minimax API를 활용한 YouTube Shorts 자동화 생성 시스템입니다.

## 주요 기능

- **모듈화된 프롬프트 시스템**: 콘텐츠 타입별로 특화된 프롬프트 지원
  - 🍳 **요리 (cooking)**: 레시피, 요리 과정, 다양한 배경 (주방/캠핑/자연/해변 등)
  - ✈️ **여행 (travel)**: 여행지 소개, 관광 명소 등 (향후 지원 예정)
  - 🍽️ **먹방 (mukbang)**: 음식 리뷰, 맛 평가 등 (향후 지원 예정)
- **동기화된 이미지-비디오 생성**: 완벽히 연결된 10개 장면
- **병렬 처리**: 최대 10개 이미지/비디오 동시 생성
- **체크포인트 시스템**: 안정적인 대량 생성
- **세션별 파일 관리**: 체계적인 다운로드 폴더 구조

## API 엔드포인트

### 1. 콘텐츠 타입 확인

```http
GET /api/content-types
```

**응답 예시:**

```json
{
  "available_types": ["cooking", "travel", "mukbang"],
  "descriptions": {
    "cooking": "요리 관련 콘텐츠 (레시피, 요리 과정 등)",
    "travel": "여행 관련 콘텐츠 (향후 지원 예정)",
    "mukbang": "먹방 관련 콘텐츠 (향후 지원 예정)"
  }
}
```

### 2. 프로젝트 생성 (프롬프트 생성)

```http
POST /api/projects/create
```

**요청 본문:**

```json
{
  "description": "닥스훈트가 프레첼 만들기",
  "content_type": "cooking" // 선택사항, 기본값: "cooking"
}
```

**응답 예시:**

```json
{
  "project_id": "uuid-here",
  "status": "prompts_generated",
  "content_type": "cooking",
  "prompts": ["프롬프트 1", "프롬프트 2", ...],
  "created_at": "2024-01-01T10:00:00"
}
```

### 3. 이미지 + 비디오 생성 (통합)

```http
POST /api/projects/{project_id}/generate-all
```

### 4. 이미지만 생성

```http
POST /api/projects/{project_id}/generate-images
```

### 5. 비디오만 생성

```http
POST /api/projects/{project_id}/generate-videos
```

## 콘텐츠 타입별 특징

### 요리 (Cooking) 🍳

- **지원 배경**: 주방, 캠핑, 숲, 해변, 정원, 피크닉
- **요리 종류**: 스튜/수프, 빵/베이킹, 파스타, 샐러드, 볶음요리
- **실제적인 요리 과정**: 재료 손질 → 조리 → 완성
- **동물 캐릭터**: 요리사 모자와 앞치마 착용

**요청 예시:**

```json
{
  "description": "골든 리트리버가 숲에서 캠핑 스튜 만들기",
  "content_type": "cooking"
}
```

### 여행 (Travel) ✈️ - 향후 지원

- 관광지 소개, 여행 과정, 문화 체험 등

### 먹방 (Mukbang) 🍽️ - 향후 지원

- 음식 리뷰, 맛 평가, 반응 등

## 프롬프트 시스템 구조

```
services/
├── openai_service.py          # 메인 서비스 (타입 선택)
└── prompts/
    ├── __init__.py
    ├── cooking_prompts.py     # 요리 전용 프롬프트
    ├── travel_prompts.py      # 여행 전용 프롬프트 (예정)
    └── mukbang_prompts.py     # 먹방 전용 프롬프트 (예정)
```

## 사용법

### 1. 환경 설정

```bash
# 환경변수 설정
export OPENAI_API_KEY="your-openai-key"
export MINIMAX_API_KEY="your-minimax-key"

# 의존성 설치
pip install -r requirements.txt
```

### 2. 서버 실행

```bash
python main.py
```

### 3. 요리 콘텐츠 생성 예시

```bash
# 1. 프로젝트 생성
curl -X POST "http://localhost:8000/api/projects/create" \
     -H "Content-Type: application/json" \
     -d '{"description": "페르시안 고양이가 베이킹하기", "content_type": "cooking"}'

# 2. 이미지+비디오 생성
curl -X POST "http://localhost:8000/api/projects/{project_id}/generate-all"
```

## 파일 구조

```
downloads/
└── {session_id}/
    ├── image_0.jpg
    ├── image_1.jpg
    ├── ...
    ├── video_0.mp4
    ├── video_1.mp4
    └── ...
```

## 기술 스택

- **AI 모델**: OpenAI GPT-4.1 (프롬프트 생성)
- **이미지 생성**: Minimax API
- **비디오 생성**: Minimax Video API
- **백엔드**: FastAPI + Python
- **비동기 처리**: asyncio, aiohttp

## 확장성

새로운 콘텐츠 타입 추가 시:

1. `services/prompts/` 에 새 프롬프트 파일 생성
2. `openai_service.py` 의 `prompt_handlers` 에 등록
3. 자동으로 API에서 사용 가능

**예시: sports_prompts.py 추가**

```python
# services/prompts/sports_prompts.py
class SportsPrompts:
    @staticmethod
    def get_system_prompt():
        return "스포츠 관련 프롬프트..."

    @staticmethod
    def get_user_prompt_template(description: str):
        return f"스포츠 시나리오: {description}"
```
