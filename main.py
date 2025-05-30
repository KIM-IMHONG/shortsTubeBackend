# app/main.py
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
import json
import asyncio
from datetime import datetime
import uuid
from dotenv import load_dotenv
import warnings

# 경고 메시지 무시
warnings.filterwarnings("ignore", message="urllib3")

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 서비스 임포트
from services.openai_service import OpenAIService
from services.minimax_service import MinimaxService
from services.file_manager import FileManager

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

# 필요한 디렉토리들이 존재하는지 확인하고 생성
os.makedirs(os.path.join(downloads_path, "minimax_images"), exist_ok=True)
os.makedirs(os.path.join(downloads_path, "videos"), exist_ok=True)

# 각 하위 폴더를 직접 마운트
minimax_images_path = os.path.join(downloads_path, "minimax_images")
videos_path = os.path.join(downloads_path, "videos")

app.mount("/minimax_images", StaticFiles(directory=minimax_images_path), name="minimax_images")
app.mount("/videos", StaticFiles(directory=videos_path), name="videos")
app.mount("/downloads", StaticFiles(directory=downloads_path), name="downloads")

print(f"✅ Static files configured:")
print(f"   /minimax_images -> {minimax_images_path}")
print(f"   /videos -> {videos_path}")
print(f"   /downloads -> {downloads_path}")

# 서비스 인스턴스
openai_service = OpenAIService()
minimax_service = MinimaxService()
file_manager = FileManager()

# 요청/응답 모델
class ProjectRequest(BaseModel):
    description: str
    
class ProjectResponse(BaseModel):
    project_id: str
    status: str
    prompts: Optional[List[str]] = None
    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    created_at: str

# 임시 저장소 (DB 대신)
projects_store = {}

@app.get("/")
async def root():
    return {"message": "YouTube Shorts Automation API", "status": "running"}

@app.post("/api/projects/create", response_model=ProjectResponse)
async def create_project(request: ProjectRequest):
    """프로젝트 생성 및 프롬프트 생성"""
    project_id = str(uuid.uuid4())
    print(f"Creating project with ID: {project_id}")
    print(f"Description: {request.description}")
    
    try:
        # 1. OpenAI로 이미지와 비디오 프롬프트 동시 생성
        print("Generating prompts...")
        image_prompts, video_prompts = await openai_service.generate_prompts(request.description)
        print(f"Generated {len(image_prompts)} image prompts and {len(video_prompts)} video prompts")
        
        # 프로젝트 정보 저장
        project_data = {
            "project_id": project_id,
            "description": request.description,
            "prompts": image_prompts,  # 이미지 프롬프트
            "video_prompts": video_prompts,  # 비디오 프롬프트 추가
            "images": [],
            "videos": [],
            "status": "prompts_generated",
            "created_at": datetime.now().isoformat()
        }
        
        projects_store[project_id] = project_data
        file_manager.save_project(project_id, project_data)
        
        # 응답에는 image prompts만 포함 (하위 호환성)
        response_data = project_data.copy()
        response_data.pop("video_prompts", None)  # 응답에서는 제거
        
        return ProjectResponse(**response_data)
        
    except Exception as e:
        print(f"Error creating project: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/generate-all")
async def generate_images_and_videos(project_id: str):
    """이미지 생성 후 자동으로 비디오 생성"""
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
                # 파일명만 추출
                filename = os.path.basename(img)
                web_accessible_images.append(f"/downloads/minimax_images/{filename}")
                actual_image_paths.append(img)  # 실제 파일 경로 저장
            else:
                print(f"Warning: Image not found: {img}")
                web_accessible_images.append("")
                actual_image_paths.append("")
        
        # 프로젝트에 이미지 저장
        project["images"] = web_accessible_images
        project["status"] = "images_generated"
        
        # 2. 생성된 이미지로 바로 비디오 생성
        print(f"Creating videos from {len(actual_image_paths)} images...")
        video_paths = await minimax_service.create_videos(actual_image_paths)
        
        # 웹 접근 가능한 비디오 경로로 변환
        web_accessible_videos = []
        for video in video_paths:
            if video and os.path.exists(video):
                filename = os.path.basename(video)
                web_accessible_videos.append(f"/downloads/videos/{filename}")
            else:
                web_accessible_videos.append("")
        
        project["videos"] = web_accessible_videos
        project["status"] = "completed"
        
        # 프로젝트 저장
        file_manager.save_project(project_id, project)
        projects_store[project_id] = project
        
        return {
            "status": "success",
            "images": web_accessible_images,
            "videos": web_accessible_videos,
            "total_generated": len([img for img in images if img])
        }
        
    except Exception as e:
        print(f"Error generating content: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/generate-images")
async def generate_images(project_id: str):
    """이미지만 생성 (개별 실행용)"""
    print(f"Generating images for project: {project_id}")
    
    if project_id not in projects_store:
        project_data = file_manager.load_project(project_id)
        if project_data:
            projects_store[project_id] = project_data
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_store[project_id]
    
    try:
        # Minimax로 이미지 생성
        print("Generating images with Minimax...")
        images = await minimax_service.generate_images(project["prompts"])
        print(f"Generated {len(images)} images")
        
        # 이미지 경로를 웹에서 접근 가능한 경로로 변환
        web_accessible_images = []
        for img in images:
            if img and os.path.exists(img):
                filename = os.path.basename(img)
                web_accessible_images.append(f"/downloads/minimax_images/{filename}")
            else:
                print(f"Warning: Image not found: {img}")
                web_accessible_images.append("")
        
        # 프로젝트 업데이트
        project["images"] = web_accessible_images
        project["status"] = "images_generated"
        
        file_manager.save_project(project_id, project)
        projects_store[project_id] = project
        
        return {
            "status": "success",
            "images": web_accessible_images,
            "total_generated": len([img for img in images if img])
        }
        
    except Exception as e:
        print(f"Error generating images: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/projects/{project_id}/generate-videos")
async def generate_videos(project_id: str):
    """비디오만 생성 (개별 실행용)"""
    print(f"Generating videos for project: {project_id}")
    
    if project_id not in projects_store:
        project_data = file_manager.load_project(project_id)
        if project_data:
            projects_store[project_id] = project_data
        else:
            raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_store[project_id]
    
    if not project.get("images"):
        raise HTTPException(status_code=400, detail="Images not generated yet")
    
    try:
        # 실제 이미지 파일 경로로 변환
        actual_image_paths = []
        for img in project["images"]:
            if img:
                # /downloads/minimax_images/filename.jpg -> 실제 경로로 변환
                filename = os.path.basename(img)
                actual_path = os.path.join(os.path.dirname(current_dir), "downloads/minimax_images", filename)
                if os.path.exists(actual_path):
                    actual_image_paths.append(actual_path)
                else:
                    actual_image_paths.append("")
            else:
                actual_image_paths.append("")
        
        print(f"Creating videos from {len(actual_image_paths)} images...")
        # Minimax로 비디오 생성
        video_paths = await minimax_service.create_videos(actual_image_paths)
        
        # 웹 접근 가능한 경로로 변환
        web_accessible_videos = []
        for video in video_paths:
            if video and os.path.exists(video):
                filename = os.path.basename(video)
                web_accessible_videos.append(f"/downloads/videos/{filename}")
        
        project["videos"] = web_accessible_videos
        project["status"] = "videos_generated"
        
        file_manager.save_project(project_id, project)
        projects_store[project_id] = project
        
        return {
            "status": "success",
            "videos": web_accessible_videos
        }
        
    except Exception as e:
        print(f"Error generating videos: {e}")
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

if __name__ == "__main__":
    import uvicorn
    
    # 프로젝트 루트 디렉토리 (app의 상위 디렉토리)
    project_root = os.path.dirname(current_dir)
    
    # 필요한 디렉토리 생성
    os.makedirs(os.path.join(project_root, "downloads/minimax_images"), exist_ok=True)
    os.makedirs(os.path.join(project_root, "downloads/videos"), exist_ok=True)
    os.makedirs(os.path.join(project_root, "projects"), exist_ok=True)
    
    print("Starting YouTube Shorts Automation API...")
    print("API URL: http://localhost:8000")
    print("Docs URL: http://localhost:8000/docs")
    print(f"Working directory: {os.getcwd()}")
    print(f"Project root: {project_root}")
    
    # reload 없이 실행 (경고 없음)
    uvicorn.run(app, host="0.0.0.0", port=8000)