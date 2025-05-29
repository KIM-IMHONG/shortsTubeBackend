import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Optional
import aiofiles
from fastapi import UploadFile

class FileManager:
    def __init__(self):
        self.base_dir = "projects"
        os.makedirs(self.base_dir, exist_ok=True)
        
    def save_project(self, project_id: str, data: Dict):
        """프로젝트 데이터를 파일로 저장"""
        project_dir = os.path.join(self.base_dir, project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        file_path = os.path.join(project_dir, "project.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def load_project(self, project_id: str) -> Optional[Dict]:
        """프로젝트 데이터 로드"""
        file_path = os.path.join(self.base_dir, project_id, "project.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
        
    def list_all_projects(self) -> List[Dict]:
        """모든 프로젝트 목록 반환"""
        projects = []
        
        for project_id in os.listdir(self.base_dir):
            project_data = self.load_project(project_id)
            if project_data:
                projects.append({
                    "project_id": project_id,
                    "description": project_data.get("description", ""),
                    "status": project_data.get("status", ""),
                    "created_at": project_data.get("created_at", "")
                })
                
        return sorted(projects, key=lambda x: x["created_at"], reverse=True)
        
    async def save_uploaded_image(self, project_id: str, index: int, file: UploadFile) -> str:
        """업로드된 이미지 저장"""
        project_dir = os.path.join(self.base_dir, project_id, "images")
        os.makedirs(project_dir, exist_ok=True)
        
        # 파일 확장자 추출
        extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"custom_image_{index}.{extension}"
        file_path = os.path.join(project_dir, filename)
        
        # 파일 저장
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
            
        return file_path
        
    def get_file_path(self, project_id: str, filename: str) -> str:
        """파일 경로 반환"""
        return os.path.join(self.base_dir, project_id, filename) 