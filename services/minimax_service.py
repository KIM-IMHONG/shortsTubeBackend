# app/services/minimax_service.py
import aiohttp
import asyncio
from typing import List, Dict
import os
import base64
import json
from datetime import datetime
import time

class MinimaxService:
    def __init__(self):
        self.api_key = os.getenv("MINIMAX_API_KEY")
        self.group_id = os.getenv("MINIMAX_GROUP_ID", "")
        self.base_url = "https://api.minimaxi.chat/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.image_dir = os.path.abspath("downloads/minimax_images")
        self.video_dir = os.path.abspath("downloads/videos")
        os.makedirs(self.image_dir, exist_ok=True)
        os.makedirs(self.video_dir, exist_ok=True)
        
    async def generate_images(self, prompts: List[str]) -> List[str]:
        """프롬프트 리스트를 받아 이미지 생성"""
        if not self.api_key:
            raise RuntimeError("MINIMAX_API_KEY not set in .env file")
            
        generated_images = []
        
        async with aiohttp.ClientSession() as session:
            for i, prompt in enumerate(prompts):
                print(f"\nGenerating image {i+1}/10 from prompt: {prompt[:50]}...")
                try:
                    image_path = await self._generate_single_image(session, prompt, i)
                    if image_path:
                        generated_images.append(image_path)
                    else:
                        print(f"Warning: Failed to generate image for prompt {i+1}")
                        generated_images.append("")
                except Exception as e:
                    print(f"Error generating image {i+1}: {e}")
                    generated_images.append("")
                    
                # API 제한 방지
                await asyncio.sleep(2)
                
        return generated_images
        
    async def _generate_single_image(self, session: aiohttp.ClientSession, prompt: str, index: int) -> str:
        """단일 프롬프트로 이미지 생성"""
        try:
            # Minimax Image Generation API 엔드포인트
            url = f"{self.base_url}/image_generation"
            
            # API 문서에 맞는 올바른 payload 구조
            payload = {
                "model": "image-01",  # 올바른 이미지 생성 모델
                "prompt": prompt[:1500],  # 최대 1500자 제한
                "aspect_ratio": "16:9",  # 기본 16:9, 다른 옵션: "1:1", "4:3", "3:2", "2:3", "3:4", "9:16", "21:9"
                "response_format": "url",  # URL 형식으로 응답 (24시간 유효)
                "n": 1,  # 생성할 이미지 수 (1-9)
                "prompt_optimizer": True  # 프롬프트 최적화 활성화
            }
            
            print(f"Calling Minimax Image API: {url}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            
            async with session.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                response_text = await response.text()
                print(f"Response status: {response.status}")
                print(f"Response text: {response_text[:500]}...")
                
                if response.status != 200:
                    print(f"API Error: {response.status} - {response_text}")
                    if response.status == 401:
                        print("Authentication failed. Please check your MINIMAX_API_KEY")
                    return ""
                    
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON response: {response_text}")
                    return ""
                
                # base_resp 체크
                if "base_resp" in result:
                    base_resp = result["base_resp"]
                    if base_resp.get("status_code") != 0:
                        print(f"API returned error: {base_resp.get('status_code')} - {base_resp.get('status_msg')}")
                        return ""
                
                # 성공적인 응답 처리
                if "data" in result:
                    data = result["data"]
                    
                    # image_urls 필드로 URL이 직접 반환되는 경우
                    if "image_urls" in data and len(data["image_urls"]) > 0:
                        image_url = data["image_urls"][0]  # 첫 번째 이미지 URL
                        print(f"Image generated successfully: {image_url}")
                        return await self._download_image(session, image_url, index)
                    
                    # task_id가 반환되는 경우 (비동기 처리)
                    elif "task_id" in data:
                        print(f"Task created with ID: {data['task_id']}")
                        image_url = await self._wait_for_image_task(session, data["task_id"])
                        if image_url:
                            return await self._download_image(session, image_url, index)
                
                print(f"Unexpected response structure: {json.dumps(result, indent=2)}")
                return ""
                
        except Exception as e:
            print(f"Error in _generate_single_image: {e}")
            import traceback
            traceback.print_exc()
            return ""
            
    async def _wait_for_image_task(self, session: aiohttp.ClientSession, task_id: str) -> str:
        """이미지 생성 작업 완료 대기"""
        max_attempts = 60  # 최대 5분 대기
        attempt = 0
        
        # 작업 상태 확인 URL - Minimax API에 맞게 수정 필요
        check_url = f"{self.base_url}/query/image_generation"
        
        while attempt < max_attempts:
            try:
                params = {"task_id": task_id}
                
                async with session.get(
                    check_url,
                    params=params,
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # base_resp 체크
                        if "base_resp" in result:
                            base_resp = result["base_resp"]
                            if base_resp.get("status_code") != 0:
                                print(f"Query error: {base_resp.get('status_code')} - {base_resp.get('status_msg')}")
                                return ""
                        
                        # 작업 완료 확인
                        if "data" in result:
                            data = result["data"]
                            status = data.get("status", "")
                            
                            if status == "finished" or status == "completed":
                                # image_urls 형식으로 반환되는 경우
                                if "image_urls" in data and len(data["image_urls"]) > 0:
                                    return data["image_urls"][0]
                                # images 형식으로 반환되는 경우
                                elif "images" in data and len(data["images"]) > 0:
                                    image_info = data["images"][0]
                                    if "url" in image_info:
                                        return image_info["url"]
                            elif status == "failed":
                                print(f"Image generation failed")
                                return ""
                            else:
                                print(f"Task status: {status} ({attempt+1}/{max_attempts})")
                        
            except Exception as e:
                print(f"Error checking task status: {e}")
                
            await asyncio.sleep(3)  # 3초마다 확인
            attempt += 1
            
        print("Image generation timeout")
        return ""
            
    async def _download_image(self, session: aiohttp.ClientSession, url: str, index: int) -> str:
        """URL에서 이미지 다운로드"""
        try:
            print(f"Downloading image from: {url}")
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status == 200:
                    content = await response.read()
                    # 파일 확장자를 URL이나 헤더에서 추출
                    content_type = response.headers.get('Content-Type', 'image/jpeg')
                    ext = 'jpg'
                    if 'png' in content_type:
                        ext = 'png'
                    elif 'webp' in content_type:
                        ext = 'webp'
                    
                    image_path = os.path.join(self.image_dir, f"image_{index}.{ext}")
                    with open(image_path, 'wb') as f:
                        f.write(content)
                    print(f"Downloaded image {index+1} to: {image_path}")
                    return image_path
                else:
                    print(f"Failed to download image: HTTP {response.status}")
                    print(f"Response: {await response.text()}")
        except asyncio.TimeoutError:
            print(f"Timeout downloading image: {url}")
        except Exception as e:
            print(f"Error downloading image: {e}")
            import traceback
            traceback.print_exc()
        return ""
        
    def _save_base64_image(self, base64_data: str, index: int) -> str:
        """Base64 데이터를 이미지 파일로 저장"""
        try:
            # base64 prefix 제거
            if "," in base64_data:
                base64_data = base64_data.split(",")[1]
                
            image_data = base64.b64decode(base64_data)
            image_path = os.path.join(self.image_dir, f"image_{index}.jpg")
            with open(image_path, 'wb') as f:
                f.write(image_data)
            print(f"Saved base64 image {index+1}")
            return image_path
        except Exception as e:
            print(f"Error saving base64 image: {e}")
            return ""
    
    async def create_videos(self, images: List[str], prompts: List[str] = None) -> List[str]:
        """이미지 리스트를 받아 비디오 생성"""
        if not self.api_key:
            raise RuntimeError("MINIMAX_API_KEY not set in .env file")
            
        video_paths = []
        
        async with aiohttp.ClientSession() as session:
            for i, image_path in enumerate(images):
                if not image_path or not os.path.exists(image_path):
                    print(f"Skipping video {i+1}: No image available")
                    video_paths.append("")
                    continue
                
                # 해당 장면의 프롬프트 가져오기
                scene_prompt = prompts[i] if prompts and i < len(prompts) else None
                    
                print(f"\nCreating video {i+1}/10 from image: {os.path.basename(image_path)}")
                try:
                    video_path = await self._create_single_video(session, image_path, i, scene_prompt)
                    if video_path:
                        video_paths.append(video_path)
                    else:
                        print(f"Warning: Failed to create video for image {i+1}")
                        video_paths.append("")
                except Exception as e:
                    print(f"Error creating video {i+1}: {e}")
                    video_paths.append("")
                    
                # API 제한 방지
                await asyncio.sleep(3)
                
        return video_paths
        
    async def _create_single_video(self, session: aiohttp.ClientSession, image_path: str, index: int, scene_prompt: str = None) -> str:
        """단일 이미지로 비디오 생성"""
        try:
            # 이미지를 base64로 인코딩
            with open(image_path, "rb") as img_file:
                image_base64 = base64.b64encode(img_file.read()).decode()
            
            # Minimax Video Generation API 호출
            url = f"{self.base_url}/video_generation"
            
            # 동적 프롬프트 생성
            if scene_prompt:
                # 비디오 전용 프롬프트가 있으면 그대로 사용
                video_prompt = scene_prompt
            else:
                # 기본 프롬프트
                video_prompt = "Create smooth, natural camera movement and bring the scene to life with subtle animations, maintaining character consistency"
            
            # Image-to-Video 모델 사용
            payload = {
                "model": "I2V-01",  # 옵션: "I2V-01-Director", "I2V-01", "I2V-01-live"
                "prompt": video_prompt,
                "first_frame_image": f"data:image/jpeg;base64,{image_base64}"  # base64 이미지 with prefix
            }
            
            print(f"Calling Minimax Video API: {url}")
            print(f"Using model: {payload['model']}")
            print(f"Video prompt: {video_prompt[:100]}...")
            
            async with session.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=600)  # 10분 타임아웃으로 증가
            ) as response:
                response_text = await response.text()
                print(f"Response status: {response.status}")
                
                if response.status != 200:
                    print(f"API Error: {response.status} - {response_text[:500]}")
                    return ""
                    
                result = json.loads(response_text)
                
                # base_resp 체크
                if "base_resp" in result:
                    base_resp = result["base_resp"]
                    if base_resp.get("status_code") != 0:
                        print(f"API returned error: {base_resp.get('status_code')} - {base_resp.get('status_msg')}")
                        return ""
                
                # 성공적인 응답 처리 - task_id 반환
                if "task_id" in result:
                    print(f"Video task created with ID: {result['task_id']}")
                    file_id = await self._wait_for_video_task(session, result["task_id"])
                    if file_id:
                        video_url = await self._get_file_url(session, file_id)
                        if video_url:
                            return await self._download_video(session, video_url, index)
                
                # task_id가 data 안에 있는 경우
                elif "data" in result and "task_id" in result["data"]:
                    task_id = result["data"]["task_id"]
                    print(f"Video task created with ID: {task_id}")
                    file_id = await self._wait_for_video_task(session, task_id)
                    if file_id:
                        video_url = await self._get_file_url(session, file_id)
                        if video_url:
                            return await self._download_video(session, video_url, index)
                    
                print(f"Unexpected video response structure: {json.dumps(result, indent=2)}")
                return ""
                
        except Exception as e:
            print(f"Error in _create_single_video: {e}")
            import traceback
            traceback.print_exc()
            return ""
            
    async def _wait_for_video_task(self, session: aiohttp.ClientSession, task_id: str) -> str:
        """비디오 생성 작업 완료 대기 - file_id 반환"""
        max_attempts = 240  # 최대 20분 대기로 늘림 (5초 간격)
        attempt = 0
        
        # 비디오 작업 상태 확인 URL
        check_url = f"{self.base_url}/query/video_generation"
        
        print(f"Starting to monitor video generation task: {task_id}")
        print("This may take 5-15 minutes depending on server load...")
        
        while attempt < max_attempts:
            try:
                params = {"task_id": task_id}
                
                async with session.get(
                    check_url,
                    params=params,
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"Task status check response: {json.dumps(result, indent=2)[:500]}")
                        
                        # base_resp 체크
                        if "base_resp" in result:
                            base_resp = result["base_resp"]
                            if base_resp.get("status_code") != 0:
                                print(f"Query error: {base_resp.get('status_code')} - {base_resp.get('status_msg')}")
                                return ""
                        
                        # 다양한 상태 필드 확인
                        status = None
                        file_id = None
                        video_url = None
                        
                        # status 확인 (여러 위치에서)
                        if "status" in result:
                            status = result["status"]
                        elif "data" in result and "status" in result["data"]:
                            status = result["data"]["status"]
                        elif "task_status" in result:
                            status = result["task_status"]
                            
                        print(f"Video task status: {status} ({attempt+1}/{max_attempts})")
                        
                        # 완료 상태 확인
                        if status in ["finished", "success", "completed", "done"]:
                            # file_id 찾기
                            if "file_id" in result:
                                return result["file_id"]
                            elif "data" in result:
                                data = result["data"]
                                if "file_id" in data:
                                    return data["file_id"]
                                elif "video" in data and isinstance(data["video"], dict):
                                    if "file_id" in data["video"]:
                                        return data["video"]["file_id"]
                                    elif "url" in data["video"]:
                                        # 직접 URL이 반환되는 경우
                                        return data["video"]["url"]
                                elif "url" in data:
                                    # 직접 URL이 반환되는 경우
                                    return data["url"]
                        
                        elif status in ["failed", "error"]:
                            error_msg = result.get("message") or result.get("error_msg") or "Unknown error"
                            print(f"Video generation failed: {error_msg}")
                            return ""
                        
                        # 진행 중인 경우 계속 대기
                        elif status in ["processing", "pending", "queued", "running"]:
                            # 진행률이 있으면 표시
                            progress = result.get("progress", 0)
                            if progress > 0:
                                print(f"Progress: {progress}%")
                            else:
                                # 5분마다 상태 메시지 출력
                                if attempt % 60 == 0:  # 5분마다
                                    elapsed_minutes = (attempt * 5) // 60
                                    print(f"Still processing... ({elapsed_minutes} minutes elapsed)")
                    else:
                        print(f"Status check failed: HTTP {response.status}")
                        
            except Exception as e:
                print(f"Error checking video task status: {e}")
                # 네트워크 에러는 무시하고 계속 시도
                
            await asyncio.sleep(5)  # 5초마다 확인
            attempt += 1
            
        print(f"Video generation timeout after {(max_attempts * 5) // 60} minutes")
        return ""
        
    async def _get_file_url(self, session: aiohttp.ClientSession, file_id: str) -> str:
        """file_id로 다운로드 URL 획득"""
        try:
            # File (Retrieve) API 사용
            url = f"{self.base_url}/files/{file_id}"
            
            async with session.get(
                url,
                headers=self.headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # URL 찾기
                    if "url" in result:
                        return result["url"]
                    elif "download_url" in result:
                        return result["download_url"]
                    elif "data" in result and "url" in result["data"]:
                        return result["data"]["url"]
                else:
                    print(f"Failed to get file URL: {response.status}")
                    
        except Exception as e:
            print(f"Error getting file URL: {e}")
            
        return ""
        
    async def _download_video(self, session: aiohttp.ClientSession, url: str, index: int) -> str:
        """URL에서 비디오 다운로드"""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    video_path = os.path.join(self.video_dir, f"video_{index}.mp4")
                    with open(video_path, 'wb') as f:
                        f.write(content)
                    print(f"Downloaded video {index+1}")
                    return video_path
                else:
                    print(f"Failed to download video: {response.status}")
        except Exception as e:
            print(f"Error downloading video: {e}")
        return ""