# app/main.py
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Union
import os
import sys
import json
import asyncio
from datetime import datetime
import uuid
from dotenv import load_dotenv
import warnings
import shutil

# 경고 메시지 무시
warnings.filterwarnings("ignore", message="urllib3")

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 서비스 임포트
from services.openai_service import OpenAIService
from services.minimax_service import MinimaxService
from services.file_manager import FileManager
from services.prompts.life_prompts import LifePromptsService

load_dotenv()

app = FastAPI(title="YouTube Shorts Automation MVP")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 설정
downloads_path = os.path.join(current_dir, "downloads")

# uploads 폴더 설정 (강아지 이미지 업로드용)
uploads_path = os.path.join(current_dir, "uploads")

# 필요한 디렉토리들이 존재하는지 확인하고 생성
os.makedirs(os.path.join(downloads_path, "minimax_images"), exist_ok=True)
os.makedirs(os.path.join(downloads_path, "videos"), exist_ok=True)
os.makedirs(os.path.join(downloads_path, "scene_images"), exist_ok=True)  # scene_images 디렉토리 추가
os.makedirs(uploads_path, exist_ok=True)

# 각 하위 폴더를 직접 마운트
minimax_images_path = os.path.join(downloads_path, "minimax_images")
videos_path = os.path.join(downloads_path, "videos")
scene_images_path = os.path.join(downloads_path, "scene_images")  # scene_images 경로 추가

app.mount("/minimax_images", StaticFiles(directory=minimax_images_path), name="minimax_images")
app.mount("/videos", StaticFiles(directory=videos_path), name="videos")
app.mount("/scene_images", StaticFiles(directory=scene_images_path), name="scene_images")  # scene_images 마운트 추가
app.mount("/downloads", StaticFiles(directory=downloads_path), name="downloads")
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")

print(f"✅ Static files configured:")
print(f"   /minimax_images -> {minimax_images_path}")
print(f"   /videos -> {videos_path}")
print(f"   /scene_images -> {scene_images_path}")  # scene_images 경로 로그 추가
print(f"   /downloads -> {downloads_path}")
print(f"   /uploads -> {uploads_path}")

# 서비스 인스턴스
openai_service = OpenAIService()
minimax_service = MinimaxService()
file_manager = FileManager()
life_prompts_service = LifePromptsService()

# 요청/응답 모델
class ProjectRequest(BaseModel):
    description: str
    content_type: Optional[str] = "cooking"  # 기본값은 요리, 나중에 "travel", "mukbang" 추가 가능
    
class CustomDogProjectRequest(BaseModel):
    description: str
    content_type: Optional[str] = "cooking"
    dog_image_filename: str  # 업로드된 강아지 이미지 파일명
    
class ProjectResponse(BaseModel):
    project_id: str
    status: str
    prompts: Optional[List[str]] = None
    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    video_prompts: Optional[List[str]] = None  # 비디오 프롬프트 추가
    dog_analysis: Optional[dict] = None  # 강아지 분석 결과 추가
    created_at: str
    content_type: Optional[str] = None  # 응답에도 content_type 추가

# 🆕 10단계 워크플로우용 요청/응답 모델
class SceneWorkflowRequest(BaseModel):
    description: str
    style_options: Optional[dict] = None
    
class SceneImageRegenerationRequest(BaseModel):
    scene_number: int
    prompt: Optional[str] = None  # None이면 원본 프롬프트 사용
    
class SceneWorkflowResponse(BaseModel):
    project_id: str
    status: str
    description: str
    scene_prompts: Optional[List[str]] = None
    scene_images: Optional[List[dict]] = None
    video_prompts: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    current_step: int
    created_at: str

# 임시 저장소 (DB 대신)
projects_store = {}

# 🔄 요청 형식 감지 함수
async def detect_request_format(request: Request):
    """요청의 Content-Type을 확인해서 JSON 또는 FormData 처리"""
    content_type = request.headers.get("content-type", "")
    
    if "application/json" in content_type:
        return "json"
    elif "multipart/form-data" in content_type:
        return "form"
    else:
        return "unknown"

@app.get("/")
async def root():
    return {"message": "YouTube Shorts Automation API", "status": "running"}

@app.get("/api/content-types")
async def get_content_types():
    """사용 가능한 콘텐츠 타입 목록 반환"""
    return {
        "available_types": openai_service.get_available_content_types(),
        "descriptions": {
            "cooking": "요리 관련 콘텐츠 (레시피, 요리 과정 등)",
            "travel": "여행 관련 콘텐츠 (향후 지원 예정)",
            "mukbang": "먹방 관련 콘텐츠 (향후 지원 예정)",
            "life": "일상 생활 콘텐츠 (쇼핑, 산책, 카페, 공원 등)"
        }
    }

@app.get("/api/prompt-types")
async def get_prompt_types():
    """프롬프트 타입별 상세 정보 및 예시 제공"""
    return {
        "prompt_types": [
            {
                "type": "cooking",
                "name": "요리 콘텐츠",
                "description": "강아지가 셰프가 되어 다양한 요리를 만드는 콘텐츠",
                "icon": "🍳",
                "examples": [
                    {
                        "title": "피자 만들기",
                        "prompt": "Shiba Inu making pizza in kitchen",
                        "description": "강아지가 피자 도우를 반죽하고 토핑을 올려 피자를 만듭니다"
                    },
                    {
                        "title": "파스타 요리",
                        "prompt": "Golden Retriever making pasta in modern kitchen",
                        "description": "강아지가 파스타를 만들고 소스를 준비합니다"
                    },
                    {
                        "title": "빵 굽기",
                        "prompt": "Corgi baking bread in cozy kitchen",
                        "description": "강아지가 반죽을 만들고 오븐에서 빵을 굽습니다"
                    }
                ],
                "suggested_descriptions": [
                    "making homemade pizza with fresh ingredients",
                    "preparing pasta with tomato sauce",
                    "baking chocolate chip cookies",
                    "making sushi rolls with precision",
                    "grilling Korean BBQ"
                ]
            },
            {
                "type": "life",
                "name": "일상 생활",
                "description": "강아지의 다양한 일상 활동을 담은 콘텐츠",
                "icon": "🐕",
                "examples": [
                    {
                        "title": "마트 쇼핑",
                        "prompt": "browsing shelves at supermarket, selecting items, and using self-checkout",
                        "description": "강아지가 마트에서 물건을 고르고 계산하는 모습"
                    },
                    {
                        "title": "해변 산책",
                        "prompt": "walking on Hawaii beach at sunset, playing with waves",
                        "description": "강아지가 하와이 해변에서 파도와 놀며 산책합니다"
                    },
                    {
                        "title": "카페 방문",
                        "prompt": "sitting at outdoor cafe, enjoying coffee and pastry",
                        "description": "강아지가 야외 카페에서 여유를 즐깁니다"
                    }
                ],
                "suggested_descriptions": [
                    "shopping at Costco and pushing cart with front paws",
                    "riding subway in New York City",
                    "playing video games on PlayStation at home",
                    "attending yoga class and doing downward dog pose",
                    "driving a toy car in the park",
                    "reading books at the library",
                    "working on laptop at home office",
                    "exercising at the gym on treadmill"
                ]
            },
            {
                "type": "mukbang",
                "name": "먹방 콘텐츠",
                "description": "강아지가 맛있는 음식을 즐기는 먹방 콘텐츠",
                "icon": "🍖",
                "examples": [
                    {
                        "title": "스테이크 먹방",
                        "prompt": "Labrador enjoying juicy steak dinner",
                        "description": "강아지가 스테이크를 맛있게 먹는 모습"
                    },
                    {
                        "title": "과일 먹방",
                        "prompt": "Poodle eating fresh fruits buffet",
                        "description": "강아지가 다양한 과일을 즐기는 모습"
                    }
                ],
                "suggested_descriptions": [
                    "enjoying Korean BBQ feast",
                    "eating sushi platter at Japanese restaurant",
                    "having afternoon tea with cakes",
                    "enjoying pizza party with friends"
                ],
                "status": "coming_soon"
            },
            {
                "type": "travel",
                "name": "여행 콘텐츠",
                "description": "강아지가 세계 각지를 여행하는 콘텐츠",
                "icon": "✈️",
                "examples": [
                    {
                        "title": "파리 여행",
                        "prompt": "Corgi visiting Eiffel Tower in Paris",
                        "description": "강아지가 에펠탑을 구경하는 모습"
                    },
                    {
                        "title": "일본 여행",
                        "prompt": "Shiba Inu at Mount Fuji with cherry blossoms",
                        "description": "강아지가 후지산과 벚꽃을 감상합니다"
                    }
                ],
                "suggested_descriptions": [
                    "exploring Times Square in New York",
                    "visiting Santorini Greece with blue domes",
                    "safari adventure in African savanna",
                    "skiing in Swiss Alps"
                ],
                "status": "coming_soon"
            }
        ]
    }

@app.get("/api/prompt-types/{prompt_type}")
async def get_prompt_type_detail(prompt_type: str):
    """특정 프롬프트 타입의 상세 정보 반환"""
    
    prompt_data = {
        "cooking": {
            "type": "cooking",
            "name": "요리 콘텐츠",
            "description": "강아지 셰프가 다양한 요리를 만드는 과정을 보여주는 콘텐츠입니다.",
            "features": [
                "전문적인 요리 기술 시연",
                "10단계 요리 과정 진행",
                "주방 도구 사용법",
                "재료 준비부터 완성까지"
            ],
            "best_for": [
                "요리 레시피 콘텐츠",
                "푸드 채널",
                "교육용 요리 영상"
            ],
            "tips": [
                "요리 종류를 구체적으로 명시하세요 (예: 'making pepperoni pizza')",
                "조리 도구를 포함하면 더 현실적입니다",
                "주방 환경을 설정할 수 있습니다 (modern kitchen, outdoor BBQ 등)"
            ]
        },
        "life": {
            "type": "life",
            "name": "일상 생활",
            "description": "강아지의 다양한 일상 활동과 모험을 담은 콘텐츠입니다.",
            "features": [
                "자유로운 활동 설정",
                "현실적인 일상 묘사",
                "다양한 장소와 상황",
                "스토리텔링 중심"
            ],
            "best_for": [
                "일상 브이로그",
                "재미있는 상황 연출",
                "스토리 기반 콘텐츠"
            ],
            "tips": [
                "구체적인 행동을 설명하세요 (예: 'pushing shopping cart at Costco')",
                "장소를 명확히 하면 더 생생합니다",
                "연속된 행동을 포함하면 스토리가 풍부해집니다"
            ]
        },
        "mukbang": {
            "type": "mukbang",
            "name": "먹방 콘텐츠",
            "description": "강아지가 맛있는 음식을 즐기는 먹방 콘텐츠입니다.",
            "features": [
                "다양한 음식 종류",
                "먹는 모습 클로즈업",
                "음식 리액션",
                "ASMR 스타일 가능"
            ],
            "best_for": [
                "먹방 채널",
                "푸드 리뷰",
                "ASMR 콘텐츠"
            ],
            "tips": [
                "음식 종류를 구체적으로 명시하세요",
                "먹는 환경을 설정할 수 있습니다",
                "음식의 양과 종류를 다양하게 할 수 있습니다"
            ],
            "status": "coming_soon"
        },
        "travel": {
            "type": "travel",
            "name": "여행 콘텐츠",
            "description": "강아지가 세계 각지의 명소를 여행하는 콘텐츠입니다.",
            "features": [
                "세계 명소 방문",
                "문화 체험",
                "모험과 탐험",
                "아름다운 풍경"
            ],
            "best_for": [
                "여행 브이로그",
                "관광 홍보",
                "교육 콘텐츠"
            ],
            "tips": [
                "구체적인 장소를 명시하세요 (예: 'Eiffel Tower in Paris')",
                "계절과 시간대를 포함하면 더 생생합니다",
                "현지 특색을 포함할 수 있습니다"
            ],
            "status": "coming_soon"
        }
    }
    
    if prompt_type not in prompt_data:
        raise HTTPException(status_code=404, detail=f"Prompt type '{prompt_type}' not found")
    
    return prompt_data[prompt_type]

@app.post("/api/upload-dog-image")
async def upload_dog_image(file: UploadFile = File(...)):
    """강아지 이미지 업로드 및 분석"""
    try:
        # 파일 확장자 확인
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise HTTPException(status_code=400, detail="Only PNG, JPG, JPEG files are allowed")
        
        # 고유 파일명 생성
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"dog_{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(uploads_path, unique_filename)
        
        # 파일 저장
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"📸 Dog image uploaded: {unique_filename}")
        
        # OpenAI Vision으로 강아지 분석
        dog_analysis = await openai_service.analyze_dog_image(file_path)
        
        return {
            "filename": unique_filename,
            "analysis": dog_analysis,
            "message": f"Dog analysis completed: {dog_analysis.get('breed', 'Unknown breed')}"
        }
        
    except Exception as e:
        print(f"Error uploading dog image: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/create")
async def create_project(request: ProjectRequest):
    """새 프로젝트 생성 - 이미지와 영상 프롬프트 함께 생성"""
    try:
        project_id = str(uuid.uuid4())
        
        # OpenAI로 이미지와 영상 프롬프트 함께 생성
        print(f"Generating image and video prompts for: {request.description}")
        image_prompts, video_prompts = await openai_service.generate_image_and_video_prompts(
            request.description, 
            request.content_type
        )
        
        # 프로젝트 데이터 생성
        project = {
            "project_id": project_id,
            "description": request.description,
            "status": "prompts_generated",  # 이미지와 영상 프롬프트 모두 생성됨
            "prompts": image_prompts,
            "video_prompts": video_prompts,  # 초기 영상 프롬프트
            "improved_video_prompts": [],   # 개선된 영상 프롬프트 (이미지 분석 후)
            "images": [],
            "videos": [],
            "created_at": datetime.now().isoformat(),
            "content_type": request.content_type,
            "dog_analysis": None  # 일반 프로젝트는 강아지 분석 없음
        }
        
        # 프로젝트 저장
        file_manager.save_project(project_id, project)
        projects_store[project_id] = project
        
        return {
            "project_id": project_id,
            "status": "prompts_generated",
            "prompts": image_prompts,
            "video_prompts": video_prompts,
            "images": [],
            "videos": [],
            "created_at": project["created_at"],
            "content_type": request.content_type
        }
        
    except Exception as e:
        print(f"Error creating project: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/create-with-custom-dog")
async def create_project_with_custom_dog(request: CustomDogProjectRequest):
    """업로드된 강아지 이미지 기반 프로젝트 생성"""
    try:
        project_id = str(uuid.uuid4())
        
        # 업로드된 강아지 이미지 경로
        dog_image_path = os.path.join(uploads_path, request.dog_image_filename)
        
        if not os.path.exists(dog_image_path):
            raise HTTPException(status_code=404, detail="Dog image not found")
        
        # 강아지 이미지 분석 (이미 분석된 경우 재사용하거나 새로 분석)
        print(f"Analyzing dog image for custom project: {request.dog_image_filename}")
        dog_analysis = await openai_service.analyze_dog_image(dog_image_path)
        
        # 커스텀 강아지 기반 프롬프트 생성
        print(f"Generating custom dog prompts for: {request.description}")
        image_prompts, video_prompts = await openai_service.generate_image_and_video_prompts_with_custom_dog(
            request.description,
            dog_analysis,
            request.content_type
        )
        
        # 프로젝트 데이터 생성
        project = {
            "project_id": project_id,
            "description": request.description,
            "status": "prompts_generated",
            "prompts": image_prompts,
            "video_prompts": video_prompts,
            "improved_video_prompts": [],
            "images": [],
            "videos": [],
            "created_at": datetime.now().isoformat(),
            "content_type": request.content_type,
            "dog_analysis": dog_analysis,  # 강아지 분석 결과 저장
            "dog_image_filename": request.dog_image_filename  # 원본 이미지 파일명 저장
        }
        
        # 프로젝트 저장
        file_manager.save_project(project_id, project)
        projects_store[project_id] = project
        
        return {
            "project_id": project_id,
            "status": "prompts_generated",
            "prompts": image_prompts,
            "video_prompts": video_prompts,
            "images": [],
            "videos": [],
            "dog_analysis": dog_analysis,
            "created_at": project["created_at"],
            "content_type": request.content_type
        }
        
    except Exception as e:
        print(f"Error creating custom dog project: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/create-with-dog-upload")
async def create_project_with_dog_upload(
    description: str = Form(...),
    content_type: str = Form("cooking"),
    file: UploadFile = File(...)
):
    """강아지 이미지 업로드와 프롬프트 생성을 한번에 처리"""
    try:
        project_id = str(uuid.uuid4())
        
        # 파일 확장자 확인
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise HTTPException(status_code=400, detail="Only PNG, JPG, JPEG files are allowed")
        
        # 고유 파일명 생성
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"dog_{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(uploads_path, unique_filename)
        
        # 파일 저장
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"📸 Dog image uploaded: {unique_filename}")
        
        # OpenAI Vision으로 강아지 분석
        dog_analysis = await openai_service.analyze_dog_image(file_path)
        
        # 커스텀 강아지 기반 프롬프트 생성
        print(f"Generating custom dog prompts for: {description}")
        image_prompts, video_prompts = await openai_service.generate_image_and_video_prompts_with_custom_dog(
            description,
            dog_analysis,
            content_type
        )
        
        # 프로젝트 데이터 생성
        project = {
            "project_id": project_id,
            "description": description,
            "status": "prompts_generated",
            "prompts": image_prompts,
            "video_prompts": video_prompts,
            "improved_video_prompts": [],
            "images": [],
            "videos": [],
            "created_at": datetime.now().isoformat(),
            "content_type": content_type,
            "dog_analysis": dog_analysis,
            "dog_image_filename": unique_filename
        }
        
        # 프로젝트 저장
        file_manager.save_project(project_id, project)
        projects_store[project_id] = project
        
        return {
            "project_id": project_id,
            "status": "prompts_generated",
            "prompts": image_prompts,
            "video_prompts": video_prompts,
            "images": [],
            "videos": [],
            "dog_analysis": dog_analysis,
            "dog_image_filename": unique_filename,
            "created_at": project["created_at"],
            "content_type": content_type
        }
        
    except Exception as e:
        print(f"Error creating project with dog upload: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/generate-images")
async def generate_images_only(project_id: str):
    """이미지 생성 후 AI가 최적 이미지 선택 (2단계)"""
    print(f"Generating images for project: {project_id}")
    
    if project_id not in projects_store:
        # 파일에서 로드 시도
        project_data = file_manager.load_project(project_id)
        if project_data:
            projects_store[project_id] = project_data
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_store[project_id]
    
    try:
        # Minimax로 4개 이미지 생성 (1개 프롬프트당 4개 이미지)
        print("Generating 4 images per prompt with Minimax...")
        image_results = await minimax_service.generate_images(project["prompts"])
        print(f"Generated image results for {len(image_results)} prompts")
        
        # 각 프롬프트에 대해 4개 이미지 중 최적 선택
        selected_images = []
        all_images = []  # 모든 이미지 저장 (선택 과정 확인용)
        
        for i, images_for_prompt in enumerate(image_results):
            if isinstance(images_for_prompt, list) and len(images_for_prompt) > 1:
                print(f"\n🔍 Selecting best image for prompt {i+1} from {len(images_for_prompt)} options...")
                
                # OpenAI가 최적 이미지 선택
                selected_image = await openai_service.select_best_image_for_video(
                    images_for_prompt,
                    project["prompts"][i],
                    project["description"]
                )
                
                selected_images.append(selected_image)
                all_images.append({
                    "prompt_index": i,
                    "all_images": images_for_prompt,
                    "selected_image": selected_image
                })
                print(f"✅ Selected image for prompt {i+1}: {os.path.basename(selected_image)}")
            else:
                # 단일 이미지인 경우
                single_image = images_for_prompt[0] if isinstance(images_for_prompt, list) else images_for_prompt
                selected_images.append(single_image)
                all_images.append({
                    "prompt_index": i,
                    "all_images": [single_image],
                    "selected_image": single_image
                })
                print(f"✅ Single image for prompt {i+1}: {os.path.basename(single_image)}")
        
        # 선택된 이미지들을 웹에서 접근 가능한 경로로 변환
        web_accessible_images = []
        actual_image_paths = []
        
        for img in selected_images:
            if img and os.path.exists(img):
                # downloads 폴더 기준으로 상대 경로 생성
                relative_path = os.path.relpath(img, downloads_path)
                web_accessible_images.append(f"/{relative_path}")
                actual_image_paths.append(img)  # 실제 파일 경로 저장
            else:
                print(f"Warning: Selected image not found: {img}")
                web_accessible_images.append("")
                actual_image_paths.append("")
        
        # 프로젝트에 선택된 이미지 저장
        project["images"] = web_accessible_images
        project["actual_image_paths"] = actual_image_paths  # 내부적으로 실제 경로 저장
        project["all_generated_images"] = all_images  # 선택 과정 기록
        project["status"] = "images_generated"
        
        # 프로젝트 저장
        file_manager.save_project(project_id, project)
        projects_store[project_id] = project
        
        return {
            "project_id": project_id,
            "status": "images_generated",
            "images": web_accessible_images,
            "selection_info": [
                {
                    "prompt_index": info["prompt_index"],
                    "total_generated": len(info["all_images"]),
                    "selected_image": f"/{os.path.relpath(info['selected_image'], downloads_path)}" if info['selected_image'] else None
                }
                for info in all_images
            ],
            "message": f"Generated and selected {len(web_accessible_images)} optimal images using AI selection"
        }
        
    except Exception as e:
        print(f"Error generating images: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/analyze-and-generate-video-prompts")
async def analyze_and_improve_video_prompts(project_id: str):
    """이미지 분석하여 영상 프롬프트 개선 (3단계)"""
    print(f"Analyzing images and improving video prompts for project: {project_id}")
    
    if project_id not in projects_store:
        # 파일에서 로드 시도
        project_data = file_manager.load_project(project_id)
        if project_data:
            projects_store[project_id] = project_data
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_store[project_id]
    
    # 이미지가 생성되지 않았으면 에러
    if not project.get("images") or not project.get("actual_image_paths"):
        raise HTTPException(status_code=400, detail="Images must be generated first")
    
    try:
        # 이미지 분석하여 영상 프롬프트 개선
        print("Improving video prompts based on generated images...")
        improved_video_prompts = await openai_service.improve_video_prompts_from_images(
            project["actual_image_paths"],
            project["video_prompts"],  # 원본 영상 프롬프트
            project["description"],
            project["content_type"]
        )
        
        # 개선된 영상 프롬프트 저장
        project["improved_video_prompts"] = improved_video_prompts
        project["status"] = "video_prompts_improved"
        
        # 프로젝트 저장
        file_manager.save_project(project_id, project)
        projects_store[project_id] = project
        
        return {
            "project_id": project_id,
            "status": "video_prompts_improved",
            "original_video_prompts": project["video_prompts"],
            "improved_video_prompts": improved_video_prompts,
            "message": f"Improved {len(improved_video_prompts)} video prompts based on image analysis"
        }
        
    except Exception as e:
        print(f"Error improving video prompts: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/generate-videos")
async def generate_videos(project_id: str):
    """개선된 영상 프롬프트로 비디오 생성 (4단계)"""
    print(f"Generating videos for project: {project_id}")
    
    if project_id not in projects_store:
        # 파일에서 로드 시도
        project_data = file_manager.load_project(project_id)
        if project_data:
            projects_store[project_id] = project_data
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_store[project_id]
    
    # 이미지와 비디오 프롬프트가 있는지 확인
    if not project.get("actual_image_paths"):
        raise HTTPException(status_code=400, detail="Images must be generated first")
    
    # 개선된 영상 프롬프트가 있으면 사용, 없으면 원본 사용
    video_prompts = project.get("improved_video_prompts") or project.get("video_prompts")
    if not video_prompts:
        raise HTTPException(status_code=400, detail="Video prompts not found")
    
    try:
        # 비디오 생성
        print(f"Creating videos from images using {'improved' if project.get('improved_video_prompts') else 'original'} prompts...")
        actual_image_paths = project["actual_image_paths"]
        
        # 이미지와 비디오 프롬프트 개수가 일치하는지 확인
        if len(actual_image_paths) != len(video_prompts):
            raise HTTPException(status_code=400, detail=f"Mismatch: {len(actual_image_paths)} images but {len(video_prompts)} video prompts")
        
        video_paths = await minimax_service.create_videos_with_optimized_prompts(actual_image_paths, video_prompts)
        
        # 웹 접근 가능한 비디오 경로로 변환
        web_accessible_videos = []
        for video in video_paths:
            if video and os.path.exists(video):
                # downloads 폴더 기준으로 상대 경로 생성
                # 예: /Users/.../downloads/videos/session_123/video_0.mp4
                # -> /videos/session_123/video_0.mp4
                relative_path = os.path.relpath(video, downloads_path)
                web_accessible_videos.append(f"/{relative_path}")
            else:
                web_accessible_videos.append("")
        
        project["videos"] = web_accessible_videos
        project["status"] = "completed"
        
        # 프로젝트 저장
        file_manager.save_project(project_id, project)
        projects_store[project_id] = project
        
        return {
            "project_id": project_id,
            "status": "completed",
            "videos": web_accessible_videos,
            "used_prompts": "improved" if project.get("improved_video_prompts") else "original",
            "message": f"Generated {len(web_accessible_videos)} videos using {'improved' if project.get('improved_video_prompts') else 'original'} prompts"
        }
        
    except Exception as e:
        print(f"Error generating videos: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# 기존 엔드포인트들 유지 (하위 호환성)
@app.post("/api/projects/{project_id}/generate-all")
async def generate_images_and_videos(project_id: str):
    """이미지 생성 후 자동으로 비디오 생성 (기존 방식)"""
    print(f"Generating images and videos for project: {project_id}")
    
    if project_id not in projects_store:
        # 파일에서 로드 시도
        project_data = file_manager.load_project(project_id)
        if project_data:
            projects_store[project_id] = project_data
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_store[project_id]
    
    try:
        # 1. Minimax로 이미지 생성
        print("Generating images with Minimax...")
        images = await minimax_service.generate_images(project["prompts"])
        print(f"Generated {len(images)} images")
        
        # 이미지 경로를 웹에서 접근 가능한 경로로 변환
        web_accessible_images = []
        actual_image_paths = []
        
        for img in images:
            if img and os.path.exists(img):
                # downloads 폴더 기준으로 상대 경로 생성
                # 예: /Users/.../downloads/minimax_images/session_123/image_0.jpg
                # -> /minimax_images/session_123/image_0.jpg
                relative_path = os.path.relpath(img, downloads_path)
                web_accessible_images.append(f"/{relative_path}")
                actual_image_paths.append(img)  # 실제 파일 경로 저장
            else:
                print(f"Warning: Image not found: {img}")
                web_accessible_images.append("")
                actual_image_paths.append("")
        
        # 프로젝트에 이미지 저장
        project["images"] = web_accessible_images
        project["actual_image_paths"] = actual_image_paths
        project["status"] = "images_generated"
        
        # 2. 이미지 분석 후 비디오 프롬프트 생성
        if actual_image_paths[0]:
            print("Analyzing image and generating video prompt...")
            video_prompt = await openai_service.analyze_image_and_generate_video_prompt(
                actual_image_paths[0], 
                project["description"], 
                project["content_type"]
            )
            project["video_prompts"] = [video_prompt]
        
        # 3. 생성된 이미지로 바로 비디오 생성
        print(f"Creating videos from {len(actual_image_paths)} images...")
        video_paths = await minimax_service.create_videos_with_prompts(actual_image_paths, project["video_prompts"])
        
        # 웹 접근 가능한 비디오 경로로 변환
        web_accessible_videos = []
        for video in video_paths:
            if video and os.path.exists(video):
                # downloads 폴더 기준으로 상대 경로 생성
                # 예: /Users/.../downloads/videos/session_123/video_0.mp4
                # -> /videos/session_123/video_0.mp4
                relative_path = os.path.relpath(video, downloads_path)
                web_accessible_videos.append(f"/{relative_path}")
            else:
                web_accessible_videos.append("")
        
        project["videos"] = web_accessible_videos
        project["status"] = "completed"
        
        # 프로젝트 저장
        file_manager.save_project(project_id, project)
        projects_store[project_id] = project
        
        return {
            "project_id": project_id,
            "status": "completed",
            "images": web_accessible_images,
            "videos": web_accessible_videos,
            "video_prompts": project.get("video_prompts", []),
            "message": f"Generated {len(web_accessible_images)} images and {len(web_accessible_videos)} videos"
        }
        
    except Exception as e:
        print(f"Error in generate-all: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """프로젝트 조회"""
    if project_id not in projects_store:
        # 파일에서 로드 시도
        project_data = file_manager.load_project(project_id)
        if project_data:
            projects_store[project_id] = project_data
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    
    return projects_store[project_id]

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """프로젝트 삭제"""
    try:
        # 메모리에서 제거
        if project_id in projects_store:
            del projects_store[project_id]
        
        # 파일에서 제거
        file_manager.delete_project(project_id)
        
        return {"message": "Project deleted successfully"}
    except Exception as e:
        print(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/projects/{project_id}/images/{image_index}")
async def update_image(project_id: str, image_index: int, file: UploadFile = File(...)):
    """이미지 수동 업데이트"""
    print(f"Updating image {image_index} for project {project_id}")
    
    if project_id not in projects_store:
        project_data = file_manager.load_project(project_id)
        if project_data:
            projects_store[project_id] = project_data
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_store[project_id]
    
    try:
        # 이미지 저장
        file_path = await file_manager.save_uploaded_image(project_id, image_index, file)
        
        # 웹 접근 가능한 경로로 변환
        web_accessible_path = f"/projects/{project_id}/images/{os.path.basename(file_path)}"
        
        # 프로젝트 업데이트
        if image_index < len(project["images"]):
            project["images"][image_index] = web_accessible_path
            file_manager.save_project(project_id, project)
            projects_store[project_id] = project
        
        return {"status": "success", "image_path": web_accessible_path}
        
    except Exception as e:
        print(f"Error updating image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects")
async def list_projects():
    """모든 프로젝트 목록"""
    try:
        # 파일 시스템에서 모든 프로젝트 로드
        all_projects = file_manager.list_all_projects()
        return {"projects": all_projects}
    except Exception as e:
        print(f"Error listing projects: {e}")
        return {"projects": []}

# 파일 서빙 (이미지/비디오)
@app.get("/projects/{project_id}/images/{filename}")
async def serve_project_image(project_id: str, filename: str):
    file_path = os.path.join("projects", project_id, "images", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

@app.post("/api/projects/{project_id}/generate-video-prompts-from-description")
async def generate_video_prompts_from_description(project_id: str):
    """설명 기반 비디오 프롬프트 생성 (이미지 분석 대체)"""
    print(f"Generating video prompts from description for project: {project_id}")
    
    if project_id not in projects_store:
        # 파일에서 로드 시도
        project_data = file_manager.load_project(project_id)
        if project_data:
            projects_store[project_id] = project_data
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_store[project_id]
    
    if not project.get("actual_image_paths") or not project["actual_image_paths"][0]:
        raise HTTPException(status_code=400, detail="No images found. Generate images first.")
    
    try:
        # 설명 기반 비디오 프롬프트 생성
        from services.prompts.cooking_prompts import CookingPrompts
        
        description = project["description"]
        video_prompt = CookingPrompts.get_improved_video_prompt(description)
        
        # 비디오 프롬프트 저장
        project["video_prompts"] = [video_prompt]
        project["status"] = "video_prompts_generated"
        
        # 프로젝트 저장
        file_manager.save_project(project_id, project)
        projects_store[project_id] = project
        
        return {
            "project_id": project_id,
            "status": "video_prompts_generated",
            "video_prompts": [video_prompt],
            "message": "Generated video prompt based on description analysis"
        }
        
    except Exception as e:
        print(f"Error generating video prompt from description: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/create-new-workflow")
async def create_new_workflow_project(
    description: str = Form(...),
    num_steps: int = Form(5),
    file: UploadFile = File(...)
):
    """새로운 4단계 워크플로우 프로젝트 생성"""
    try:
        project_id = str(uuid.uuid4())
        
        # 파일 확장자 확인
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            raise HTTPException(status_code=400, detail="Only PNG, JPG, JPEG files are allowed")
        
        # 고유 파일명 생성
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"dog_{project_id}{file_extension}"
        file_path = os.path.join(uploads_path, unique_filename)
        
        # 파일 저장
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"📸 Dog image uploaded for new workflow: {unique_filename}")
        
        # 프로젝트 데이터 생성
        project = {
            "project_id": project_id,
            "description": description,
            "num_steps": num_steps,
            "dog_image_path": unique_filename,
            "workflow_type": "new_4_step",
            "status": "created",
            "step_prompts": [],
            "generated_images": [],
            "selected_image_index": None,
            "selection_reason": "",
            "video_prompt": "",
            "final_video_path": None,
            "created_at": datetime.now().isoformat()
        }
        
        # 프로젝트 저장
        file_manager.save_project(project_id, project)
        projects_store[project_id] = project
        
        return {
            "project_id": project_id,
            "description": description,
            "num_steps": num_steps,
            "dog_image": unique_filename,
            "workflow_type": "new_4_step",
            "status": "created",
            "created_at": project["created_at"]
        }
        
    except Exception as e:
        print(f"Error creating new workflow project: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/create-video-sequence")
async def create_video_sequence_project(
    description: str = Form(...),
    content_type: str = Form("cooking"),
    file: UploadFile = File(...)
):
    """새로운 워크플로우로 리다이렉트: 강아지 이미지 업로드 + 4단계 워크플로우"""
    try:
        # 새로운 워크플로우 API로 리다이렉트
        result = await create_new_workflow_project(description, 5, file)
        
        # 기존 응답 형식과 호환되도록 변환
        return {
            "id": result["project_id"],
            "description": description,
            "content_type": content_type,
            "status": "created",
            "dog_image_path": result["dog_image"],
            "workflow_type": "video_sequence",
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error creating video sequence project: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/execute-complete-workflow")
async def execute_complete_workflow(project_id: str):
    """완전한 4단계 워크플로우 실행"""
    try:
        if project_id not in projects_store:
            project_data = file_manager.load_project(project_id)
            if project_data:
                projects_store[project_id] = project_data
            else:
                raise HTTPException(status_code=404, detail="Project not found")
        
        project = projects_store[project_id]
        
        if project.get("workflow_type") != "new_4_step":
            raise HTTPException(status_code=400, detail="This endpoint is for new 4-step workflow only")
        
        # 강아지 이미지 경로
        dog_image_path = os.path.join(uploads_path, project["dog_image_path"])
        if not os.path.exists(dog_image_path):
            raise HTTPException(status_code=404, detail="Dog image not found")
        
        print(f"🚀 Starting complete 4-step workflow for project: {project_id}")
        
        # 완전한 워크플로우 실행
        result = await life_prompts_service.execute_complete_workflow(
            dog_image_path, 
            project["description"], 
            project["num_steps"]
        )
        
        # 프로젝트 데이터 업데이트
        project.update({
            "status": result["status"],
            "step_prompts": result["step_prompts"],
            "generated_images": [os.path.relpath(img, downloads_path) for img in result["generated_images"]] if result["generated_images"] else [],
            "selected_image_index": result["selected_image_index"],
            "selection_reason": result["selection_reason"],
            "video_prompt": result["video_prompt"],
            "final_video_path": os.path.relpath(result["final_video_path"], downloads_path) if result["final_video_path"] else None,
            "error": result["error"],
            "updated_at": datetime.now().isoformat()
        })
        
        # 프로젝트 저장
        projects_store[project_id] = project
        file_manager.save_project(project_id, project)
        
        return {
            "project_id": project_id,
            "status": result["status"],
            "workflow_type": "new_4_step_complete",
            "step_prompts": result["step_prompts"],
            "generated_images": project["generated_images"],
            "selected_image_index": result["selected_image_index"],
            "selection_reason": result["selection_reason"],
            "video_prompt": result["video_prompt"],
            "final_video_path": project["final_video_path"],
            "error": result["error"],
            "message": "Complete 4-step workflow executed" + (" successfully" if result["status"] == "completed" else " with errors")
        }
        
    except Exception as e:
        print(f"Error executing complete workflow: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/execute-step/{step}")
async def execute_workflow_step(project_id: str, step: int):
    """단계별 워크플로우 실행 (1-4단계)"""
    try:
        if project_id not in projects_store:
            project_data = file_manager.load_project(project_id)
            if project_data:
                projects_store[project_id] = project_data
            else:
                raise HTTPException(status_code=404, detail="Project not found")
        
        project = projects_store[project_id]
        
        if project.get("workflow_type") != "new_4_step":
            raise HTTPException(status_code=400, detail="This endpoint is for new 4-step workflow only")
        
        # 강아지 이미지 경로
        dog_image_path = os.path.join(uploads_path, project["dog_image_path"])
        if not os.path.exists(dog_image_path):
            raise HTTPException(status_code=404, detail="Dog image not found")
        
        print(f"🔄 Executing step {step} for project: {project_id}")
        
        # 이전 단계 데이터 준비
        previous_data = None
        if step > 1:
            previous_data = {
                "step_prompts": project.get("step_prompts", []),
                "generated_images": [os.path.join(downloads_path, img) for img in project.get("generated_images", [])],
                "selected_image_index": project.get("selected_image_index"),
                "selected_image_path": os.path.join(downloads_path, project["generated_images"][project["selected_image_index"]]) if project.get("selected_image_index") is not None and project.get("generated_images") else None,
                "video_prompt": project.get("video_prompt", "")
            }
        
        # 단계별 실행
        result = await life_prompts_service.execute_step_by_step(
            dog_image_path,
            project["description"],
            step,
            previous_data,
            project["num_steps"]
        )
        
        # 결과에 따라 프로젝트 데이터 업데이트
        if result["status"] == "success":
            if step == 1:
                project["step_prompts"] = result["data"]["step_prompts"]
            elif step == 2:
                project["generated_images"] = [os.path.relpath(img, downloads_path) for img in result["data"]["generated_images"]]
            elif step == 3:
                project["selected_image_index"] = result["data"]["selected_image_index"]
                project["selection_reason"] = result["data"]["selection_reason"]
                project["video_prompt"] = result["data"]["video_prompt"]
            elif step == 4:
                project["final_video_path"] = os.path.relpath(result["data"]["final_video_path"], downloads_path)
                project["status"] = "completed"
            
            project["updated_at"] = datetime.now().isoformat()
            
            # 프로젝트 저장
            projects_store[project_id] = project
            file_manager.save_project(project_id, project)
        
        return {
            "project_id": project_id,
            "step": step,
            "status": result["status"],
            "data": result.get("data", {}),
            "message": result.get("message", f"Step {step} executed"),
            "project_status": project.get("status", "processing")
        }
        
    except Exception as e:
        print(f"Error executing step {step}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/create-direct-video")
async def create_direct_video_project(
    prompts: str = Form(...),  # 사용자가 입력한 프롬프트들 (JSON 문자열)
    files: List[UploadFile] = File(...),
    description: str = Form("")  # 옵셔널로 변경, 기본값은 빈 문자열
):
    """
    여러 이미지와 사용자 입력 프롬프트로 영상 생성 프로젝트 생성
    """
    try:
        print(f"🔍 Request received:")
        print(f"  - description: '{description}'")
        print(f"  - prompts: {prompts}")
        print(f"  - files count: {len(files) if files else 0}")
        
        if files:
            for i, file in enumerate(files):
                print(f"  - file {i+1}: {file.filename} ({file.content_type}) size: {file.size if hasattr(file, 'size') else 'unknown'}")
        
        if not files:
            raise HTTPException(status_code=400, detail="최소 1개의 이미지가 필요합니다")
        
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="최대 10개의 이미지까지 업로드할 수 있습니다")
        
        print(f"📝 Received {len(files)} files and prompts: {prompts[:100]}...")
        
        # 프롬프트 파싱
        try:
            user_prompts = json.loads(prompts)
            if not isinstance(user_prompts, list):
                raise HTTPException(status_code=400, detail="프롬프트는 배열 형태여야 합니다")
            
            if len(user_prompts) != len(files):
                raise HTTPException(status_code=400, detail=f"이미지 개수({len(files)})와 프롬프트 개수({len(user_prompts)})가 일치하지 않습니다")
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            raise HTTPException(status_code=400, detail="잘못된 프롬프트 형식입니다")
        
        # 프로젝트 ID 생성
        project_id = str(uuid.uuid4())
        project_dir = os.path.join("projects", project_id)
        uploads_dir = os.path.join(project_dir, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        
        # 여러 이미지 저장
        saved_image_paths = []
        for i, file in enumerate(files):
            if not file.content_type or not file.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail=f"파일 {i+1}은 이미지 파일이 아닙니다")
            
            # 확장자 추출
            file_extension = file.filename.split(".")[-1] if file.filename and "." in file.filename else "jpg"
            image_filename = f"input_image_{i+1}.{file_extension}"
            image_path = os.path.join(uploads_dir, image_filename)
            
            # 이미지 저장
            content = await file.read()
            with open(image_path, "wb") as f:
                f.write(content)
            
            saved_image_paths.append(image_path)
            print(f"💾 Saved image {i+1}: {image_filename}")
        
        # 설명이 비어있으면 기본값 설정
        if not description.strip():
            description = f"{len(saved_image_paths)}개 이미지로 구성된 스토리 영상"
        
        # 프로젝트 정보 저장
        project_data = {
            "project_id": project_id,
            "description": description,
            "workflow_type": "direct_video_with_prompts",
            "status": "created",
            "created_at": datetime.now().isoformat(),
            "image_paths": saved_image_paths,
            "user_prompts": user_prompts,  # 사용자가 입력한 프롬프트들
            "num_images": len(saved_image_paths),
            "generated_videos": [],
            "message": f"{len(saved_image_paths)}개 이미지와 프롬프트가 업로드되었습니다"
        }
        
        # 프로젝트 파일 저장
        project_file = os.path.join(project_dir, "project.json")
        with open(project_file, "w", encoding="utf-8") as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Direct video project with user prompts created: {project_id} with {len(saved_image_paths)} images")
        
        return {
            "project_id": project_id,
            "message": f"{len(saved_image_paths)}개 이미지와 프롬프트 업로드 완료",
            "status": "created",
            "num_images": len(saved_image_paths),
            "user_prompts": user_prompts
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating direct video project with prompts: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"프로젝트 생성 실패: {str(e)}")

@app.post("/api/projects/{project_id}/execute-direct-video")
async def execute_direct_video_generation(project_id: str):
    """
    직접 영상 생성 실행 (사용자 프롬프트 사용)
    """
    try:
        # 프로젝트 정보 로드
        project_dir = os.path.join("projects", project_id)
        project_file = os.path.join(project_dir, "project.json")
        
        if not os.path.exists(project_file):
            raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다")
        
        with open(project_file, "r", encoding="utf-8") as f:
            project_data = json.load(f)
        
        if project_data["workflow_type"] != "direct_video_with_prompts":
            raise HTTPException(status_code=400, detail="잘못된 워크플로우 타입입니다")
        
        image_paths = project_data["image_paths"]
        user_prompts = project_data["user_prompts"]
        
        print(f"🎬 Generating {len(user_prompts)} videos using user-provided prompts...")
        
        # 사용자 프롬프트를 그대로 사용해서 영상 생성
        minimax_service = MinimaxService()
        generated_videos = await minimax_service.generate_videos_from_images_and_prompts(
            image_paths, user_prompts
        )
        
        # 웹 접근 가능한 경로로 변환
        web_accessible_videos = []
        for video_path in generated_videos:
            if video_path and os.path.exists(video_path):
                relative_path = os.path.relpath(video_path, downloads_path)
                web_accessible_videos.append(f"/{relative_path}")
            else:
                web_accessible_videos.append("")
        
        # 프로젝트 정보 업데이트
        project_data.update({
            "generated_videos": web_accessible_videos,
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "message": f"{len(web_accessible_videos)}개의 영상이 생성되었습니다"
        })
        
        # 프로젝트 파일 저장
        with open(project_file, "w", encoding="utf-8") as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Direct video generation completed: {len(web_accessible_videos)} videos")
        
        return {
            "project_id": project_id,
            "message": f"{len(web_accessible_videos)}개 영상 생성 완료",
            "status": "completed",
            "story_prompts": user_prompts,  # 사용자가 입력한 프롬프트 반환
            "generated_videos": web_accessible_videos,
            "num_videos": len(web_accessible_videos)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error executing direct video generation: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"영상 생성 실패: {str(e)}")

# 🆕 1단계: 10단계 장면 프롬프트 생성 및 프로젝트 생성 (JSON + FormData 지원)
@app.post("/api/scene-projects/create")
async def create_scene_project(
    request: Request,
    # JSON 형식 처리
    json_data: Optional[SceneWorkflowRequest] = None,
    # FormData 형식 처리
    description: Optional[str] = Form(None),
    style_options: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    10단계 장면 기반 프로젝트 생성 및 장면 프롬프트 생성 (JSON/FormData 자동 감지)
    """
    try:
        project_id = str(uuid.uuid4())
        
        # 요청 형식 감지
        format_type = await detect_request_format(request)
        print(f"🔍 Detected request format: {format_type}")
        
        # JSON 형식 처리
        if format_type == "json":
            try:
                body = await request.body()
                json_content = json.loads(body.decode())
                description = json_content.get("description")
                style_options_data = json_content.get("style_options", {})
                reference_image_path = None
                print(f"📥 JSON request processed")
            except Exception as e:
                print(f"❌ JSON parsing error: {e}")
                raise HTTPException(status_code=400, detail="Invalid JSON format")
        
        # FormData 형식 처리
        elif format_type == "form":
            if not description:
                raise HTTPException(status_code=400, detail="Description is required")
            
            # 스타일 옵션 파싱
            try:
                style_options_data = json.loads(style_options) if style_options else {}
            except json.JSONDecodeError:
                style_options_data = {}
            
            # 참고 이미지 처리
            reference_image_path = None
            if file and file.filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"reference_{timestamp}_{file.filename}"
                reference_image_path = os.path.join(uploads_path, filename)
                
                with open(reference_image_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                print(f"📷 Reference image uploaded: {filename}")
            
            print(f"📥 FormData request processed")
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported request format")
        
        if not description:
            raise HTTPException(status_code=400, detail="Description is required")
        
        print(f"🆕 Creating scene project: {project_id}")
        print(f"📝 Description: {description}")
        print(f"🎨 Style options: {style_options_data}")
        
        # 1단계: 10단계 장면 프롬프트 생성 (실제 강아지 사진 분석 포함)
        scene_prompts = minimax_service.generate_10_step_scene_prompts(
            description, 
            reference_image_path,  # 🆕 참고 이미지 전달
            style_options_data
        )
        
        # 프로젝트 정보 저장
        project_data = {
            "project_id": project_id,
            "description": description,
            "style_options": style_options_data,
            "reference_image_path": reference_image_path,  # 🆕 참고 이미지 경로 저장
            "scene_prompts": scene_prompts,
            "scene_images": [],
            "video_prompts": [],
            "videos": [],
            "current_step": 1,  # 1단계 완료
            "created_at": datetime.now().isoformat(),
            "status": "scene_prompts_generated"
        }
        
        projects_store[project_id] = project_data
        
        return SceneWorkflowResponse(
            project_id=project_id,
            status="scene_prompts_generated",
            description=description,
            scene_prompts=scene_prompts,
            current_step=1,
            created_at=project_data["created_at"]
        )
        
    except Exception as e:
        print(f"❌ Error creating scene project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scene-projects/{project_id}/generate-images")
async def generate_scene_images(project_id: str, file: UploadFile = File(None)):
    """
    프로젝트의 장면별 이미지 생성 (1단계에서 업로드된 참고 이미지 사용)
    """
    try:
        if project_id not in projects_store:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_data = projects_store[project_id]
        scene_prompts = project_data.get("scene_prompts", [])
        existing_reference_image = project_data.get("reference_image_path")
        
        if not scene_prompts:
            raise HTTPException(status_code=400, detail="Scene prompts not found. Please complete step 1 first.")
        
        # 참고 이미지 처리 (1단계 이미지 우선, 새 업로드 이미지는 보조)
        reference_image_path = existing_reference_image
        
        # 새로운 참고 이미지가 업로드된 경우 (선택사항)
        if file and file.filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reference_step2_{timestamp}_{file.filename}"
            new_reference_path = os.path.join(uploads_path, filename)
            
            with open(new_reference_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            print(f"📷 Additional reference image uploaded for step 2: {filename}")
            print(f"🔄 Using step 1 reference image as primary: {existing_reference_image}")
            # 1단계 이미지를 우선 사용
            
        print(f"🎨 Generating scene images for project: {project_id}")
        print(f"📷 Using reference image: {reference_image_path}")
        
        # 2단계: 장면별 이미지 생성 (1단계 참고 이미지 사용)
        scene_images = await minimax_service.generate_scene_images_with_regeneration(
            scene_prompts,
            reference_image_path,
            "downloads/scene_images"
        )
        
        # 프로젝트 데이터 업데이트
        project_data["scene_images"] = scene_images
        project_data["current_step"] = 2
        project_data["status"] = "scene_images_generated"
        
        return SceneWorkflowResponse(
            project_id=project_id,
            status="scene_images_generated",
            description=project_data["description"],
            scene_prompts=scene_prompts,
            scene_images=scene_images,
            current_step=2,
            created_at=project_data["created_at"]
        )
        
    except Exception as e:
        print(f"❌ Error generating scene images: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scene-projects/{project_id}/regenerate-image")
async def regenerate_scene_image(project_id: str, request: SceneImageRegenerationRequest):
    """
    특정 장면의 이미지 재생성
    """
    try:
        if project_id not in projects_store:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_data = projects_store[project_id]
        scene_images = project_data.get("scene_images", [])
        
        if not scene_images:
            raise HTTPException(status_code=400, detail="Scene images not found. Please complete step 2 first.")
        
        # 해당 장면 찾기
        target_scene = None
        for scene in scene_images:
            if scene["scene_number"] == request.scene_number:
                target_scene = scene
                break
        
        if not target_scene:
            raise HTTPException(status_code=404, detail=f"Scene {request.scene_number} not found")
        
        print(f"🔄 Regenerating image for Scene {request.scene_number}")
        
        # 이미지 재생성
        regenerated_image = await minimax_service.regenerate_scene_image(
            request.scene_number,
            request.prompt,
            target_scene["prompt"],
            project_data.get("reference_image_path"),
            "downloads/scene_images"
        )
        
        # 프로젝트 데이터에서 해당 장면 업데이트
        for i, scene in enumerate(scene_images):
            if scene["scene_number"] == request.scene_number:
                scene_images[i] = regenerated_image
                break
        
        project_data["scene_images"] = scene_images
        
        return {"status": "regenerated", "scene_image": regenerated_image}
        
    except Exception as e:
        print(f"❌ Error regenerating scene image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scene-projects/{project_id}/generate-video-prompts")
async def generate_scene_video_prompts(project_id: str):
    """
    장면 이미지들을 기반으로 영상용 프롬프트 생성
    """
    try:
        if project_id not in projects_store:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_data = projects_store[project_id]
        scene_images = project_data.get("scene_images", [])
        
        if not scene_images:
            raise HTTPException(status_code=400, detail="Scene images not found. Please complete step 2 first.")
        
        print(f"🎬 Generating video prompts for project: {project_id}")
        
        # 3단계: 영상용 프롬프트 생성
        video_prompts = minimax_service.generate_video_prompts_from_scenes(scene_images)
        
        # 프로젝트 데이터 업데이트
        project_data["video_prompts"] = video_prompts
        project_data["current_step"] = 3
        project_data["status"] = "video_prompts_generated"
        
        return SceneWorkflowResponse(
            project_id=project_id,
            status="video_prompts_generated",
            description=project_data["description"],
            scene_prompts=project_data["scene_prompts"],
            scene_images=scene_images,
            video_prompts=video_prompts,
            current_step=3,
            created_at=project_data["created_at"]
        )
        
    except Exception as e:
        print(f"❌ Error generating video prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scene-projects/{project_id}/generate-videos")
async def generate_scene_videos(project_id: str):
    """
    장면별 영상 생성 (S2V-01 모델 사용)
    """
    try:
        if project_id not in projects_store:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_data = projects_store[project_id]
        scene_images = project_data.get("scene_images", [])
        video_prompts = project_data.get("video_prompts", [])
        
        if not scene_images or not video_prompts:
            raise HTTPException(status_code=400, detail="Scene images and video prompts required. Please complete steps 2 and 3 first.")
        
        print(f"🎬 Generating videos for project: {project_id}")
        
        # 성공한 이미지들만 필터링
        successful_images = [img for img in scene_images if img["status"] == "success"]
        successful_image_paths = [img["filepath"] for img in successful_images]
        
        # 해당 이미지들의 비디오 프롬프트만 필터링
        filtered_video_prompts = []
        for img in scene_images:
            if img["status"] == "success":
                scene_idx = img["scene_number"] - 1
                if scene_idx < len(video_prompts) and video_prompts[scene_idx]:
                    filtered_video_prompts.append(video_prompts[scene_idx])
        
        if not successful_image_paths:
            raise HTTPException(status_code=400, detail="No successful images found for video generation")
        
        # 4단계: S2V-01 모델로 영상 생성
        generated_videos = await minimax_service.generate_videos_from_images_and_prompts(
            successful_image_paths,
            filtered_video_prompts,
            "downloads/videos"
        )
        
        # 프로젝트 데이터 업데이트
        project_data["videos"] = generated_videos
        project_data["current_step"] = 4
        project_data["status"] = "videos_generated"
        
        return SceneWorkflowResponse(
            project_id=project_id,
            status="videos_generated",
            description=project_data["description"],
            scene_prompts=project_data["scene_prompts"],
            scene_images=scene_images,
            video_prompts=video_prompts,
            videos=generated_videos,
            current_step=4,
            created_at=project_data["created_at"]
        )
        
    except Exception as e:
        print(f"❌ Error generating videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scene-projects/{project_id}")
async def get_scene_project(project_id: str):
    """장면 프로젝트 정보 조회"""
    if project_id not in projects_store:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_data = projects_store[project_id]
    
    return SceneWorkflowResponse(
        project_id=project_id,
        status=project_data["status"],
        description=project_data["description"],
        scene_prompts=project_data.get("scene_prompts"),
        scene_images=project_data.get("scene_images"),
        video_prompts=project_data.get("video_prompts"),
        videos=project_data.get("videos"),
        current_step=project_data["current_step"],
        created_at=project_data["created_at"]
    )

@app.get("/api/scene-projects")
async def list_scene_projects():
    """장면 프로젝트 목록 조회"""
    scene_projects = {}
    for project_id, project_data in projects_store.items():
        if "scene_prompts" in project_data:  # 장면 프로젝트인지 확인
            scene_projects[project_id] = {
                "project_id": project_id,
                "description": project_data["description"],
                "status": project_data["status"],
                "current_step": project_data["current_step"],
                "created_at": project_data["created_at"]
            }
    
    return {"scene_projects": scene_projects}

if __name__ == "__main__":
    import uvicorn
    
    # 프로젝트 루트 디렉토리 (app의 상위 디렉토리)
    project_root = os.path.dirname(current_dir)
    
    # 필요한 디렉토리 생성
    os.makedirs(os.path.join(project_root, "downloads/minimax_images"), exist_ok=True)
    os.makedirs(os.path.join(project_root, "downloads/videos"), exist_ok=True)
    os.makedirs(os.path.join(project_root, "downloads/scene_images"), exist_ok=True)  # scene_images 디렉토리 추가
    os.makedirs(os.path.join(project_root, "projects"), exist_ok=True)
    
    print("Starting YouTube Shorts Automation API...")
    print("API URL: http://localhost:8000")
    print("Docs URL: http://localhost:8000/docs")
    print(f"Working directory: {os.getcwd()}")
    print(f"Project root: {project_root}")
    
    # reload 없이 실행 (경고 없음)
    uvicorn.run(app, host="0.0.0.0", port=8000)