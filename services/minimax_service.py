# app/services/minimax_service.py
import os
import requests
import base64
import asyncio
from typing import List, Dict, Optional, Tuple
import time
import json
from datetime import datetime

class MinimaxService:
    def __init__(self):
        self.api_key = os.getenv("MINIMAX_API_KEY")
        self.base_url = "https://api.minimaxi.chat/v1"
        self.image_url = f"{self.base_url}/image_generation"
        self.video_url = f"{self.base_url}/video_generation"
        self.query_url = f"{self.base_url}/query/video_generation"
        self.files_url = f"{self.base_url}/files/retrieve"  # 🆕 정확한 파일 다운로드 엔드포인트
        
    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def _poll_task_status(self, task_id: str, max_wait_time: int = 600) -> Optional[Dict]:
        """
        작업 상태를 폴링하여 완료될 때까지 기다립니다.
        
        Args:
            task_id: 비디오 생성 작업 ID
            max_wait_time: 최대 대기 시간 (초)
            
        Returns:
            완료된 작업 정보 또는 None (실패시)
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = requests.get(
                    f"{self.query_url}?task_id={task_id}",
                    headers=self._get_headers(),
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get("status", "")
                    
                    print(f"Task {task_id} status: {status}")
                    
                    if status == "Success":
                        print(f"✅ Task {task_id} completed successfully")
                        return result
                    elif status == "Failed":
                        print(f"❌ Task {task_id} failed")
                        return None
                    elif status in ["Queued", "Preparing", "Processing"]:
                        print(f"⏳ Task {task_id} still processing... waiting 10 seconds")
                        await asyncio.sleep(10)
                    else:
                        print(f"⚠️ Unknown status: {status}")
                        await asyncio.sleep(10)
                else:
                    print(f"❌ Failed to query task status: {response.status_code}")
                    print(f"Response: {response.text}")
                    await asyncio.sleep(10)
                    
            except Exception as e:
                print(f"❌ Error polling task status: {e}")
                await asyncio.sleep(10)
        
        print(f"⏰ Task {task_id} timed out after {max_wait_time} seconds")
        return None
    
    async def _download_video_by_file_id(self, file_id: str, output_dir: str) -> Optional[str]:
        """
        file_id를 사용하여 비디오를 다운로드합니다.
        
        Args:
            file_id: 파일 ID
            output_dir: 저장 디렉토리
            
        Returns:
            다운로드된 파일 경로 또는 None
        """
        try:
            print(f"📁 Getting file info for file_id: {file_id}")
            
            # MiniMax 파일 정보 조회 API
            response = requests.get(
                f"{self.files_url}?file_id={file_id}",
                headers=self._get_headers(),
                timeout=30
            )
            
            print(f"File info response status: {response.status_code}")
            print(f"File info response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                
                # 응답 구조 확인
                print(f"File info structure: {list(result.keys()) if isinstance(result, dict) else type(result)}")
                
                # 다양한 가능한 다운로드 URL 경로 시도
                download_url = None
                
                # 방법 1: 직접 다운로드 URL
                if isinstance(result, dict):
                    download_url = (
                        result.get("download_url") or
                        result.get("file_url") or
                        result.get("url") or
                        result.get("cdn_url") or
                        (result.get("file", {}).get("download_url") if result.get("file") else None) or
                        (result.get("data", {}).get("download_url") if result.get("data") else None)
                    )
                
                if download_url:
                    print(f"📥 Found download URL: {download_url[:100]}...")
                    
                    # 실제 비디오 파일 다운로드
                    video_response = requests.get(download_url, timeout=120)
                    
                    if video_response.status_code == 200:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"video_{timestamp}_{file_id}.mp4"
                        
                        os.makedirs(output_dir, exist_ok=True)
                        filepath = os.path.join(output_dir, filename)
                        
                        with open(filepath, "wb") as f:
                            f.write(video_response.content)
                        
                        file_size = len(video_response.content)
                        print(f"✅ Video downloaded: {filename} ({file_size} bytes)")
                        return filepath
                    else:
                        print(f"❌ Failed to download video file: {video_response.status_code}")
                        print(f"Download URL: {download_url}")
                else:
                    print(f"❌ No download URL found in response")
                    print(f"Available keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                    
                    # 대안: file_id 자체가 다운로드 URL일 수 있음
                    if file_id.startswith(('http://', 'https://')):
                        print(f"🔄 Trying file_id as direct URL: {file_id}")
                        video_response = requests.get(file_id, timeout=120)
                        
                        if video_response.status_code == 200:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"video_{timestamp}_direct.mp4"
                            
                            os.makedirs(output_dir, exist_ok=True)
                            filepath = os.path.join(output_dir, filename)
                            
                            with open(filepath, "wb") as f:
                                f.write(video_response.content)
                            
                            file_size = len(video_response.content)
                            print(f"✅ Video downloaded directly: {filename} ({file_size} bytes)")
                            return filepath
                        else:
                            print(f"❌ Direct download also failed: {video_response.status_code}")
            else:
                print(f"❌ Failed to get file info: {response.status_code}")
                print(f"Error response: {response.text}")
                
                # 대안: 다른 파일 조회 방식 시도
                alternative_urls = [
                    f"{self.base_url}/files/{file_id}",
                    f"{self.base_url}/file/retrieve?file_id={file_id}",
                    f"{self.base_url}/files?file_id={file_id}"
                ]
                
                for alt_url in alternative_urls:
                    print(f"🔄 Trying alternative URL: {alt_url}")
                    try:
                        alt_response = requests.get(alt_url, headers=self._get_headers(), timeout=30)
                        if alt_response.status_code == 200:
                            print(f"✅ Alternative URL worked: {alt_response.text[:200]}...")
                            # 성공한 경우 재귀 호출하여 다운로드 시도
                            break
                    except Exception as e:
                        print(f"Alternative URL failed: {e}")
                        continue
                
        except Exception as e:
            print(f"❌ Error downloading video: {e}")
            
        return None

    async def generate_images_from_prompts_and_reference(self, prompts: List[str], reference_image_path: str, output_dir: str = "downloads/minimax_images") -> List[str]:
        """
        2단계: 생성된 프롬프트들과 참고 이미지를 사용하여 이미지들을 생성
        
        Args:
            prompts: 1단계에서 생성된 프롬프트들
            reference_image_path: 참고할 원본 강아지 사진
            output_dir: 이미지 저장 디렉토리
            
        Returns:
            List of generated image file paths
        """
        
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = os.path.join(output_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        print(f"🎨 Generating {len(prompts)} images with reference image...")
        print(f"📁 Images will be saved to: {session_dir}/")
        
        try:
            # 참고 이미지를 base64로 인코딩
            with open(reference_image_path, "rb") as image_file:
                reference_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error reading reference image: {e}")
            reference_base64 = None
        
        generated_paths = []
        
        for i, prompt in enumerate(prompts):
            try:
                print(f"[Image {i+1}/{len(prompts)}] 🚀 Starting generation...")
                print(f"  Prompt: {prompt[:50]}...")
                print(f"  API URL: {self.image_url}")
                print(f"  API Key present: {'✅' if self.api_key else '❌'}")
                
                # 참고 이미지가 있으면 포함
                payload = {
                    "model": "image-01",
                    "prompt": prompt,  # 간단한 프롬프트 그대로 사용
                    "n": 1
                }
                
                # 참고 이미지 추가 (있을 경우)
                if reference_base64:
                    payload["subject_reference"] = [
                        {
                            "type": "person",  # character → person으로 변경 (더 현실적)
                            "image_file": f"data:image/jpeg;base64,{reference_base64}"
                        }
                    ]
                    print(f"[Image {i+1}/{len(prompts)}] 📷 Reference image included (size: {len(reference_base64)} chars)")
                else:
                    print(f"[Image {i+1}/{len(prompts)}] ⚠️ No reference image provided")
                
                print(f"[Image {i+1}/{len(prompts)}] 📤 Payload: {{'model': '{payload['model']}', 'prompt': '{prompt[:50]}...', 'subject_reference': {'YES' if 'subject_reference' in payload else 'NO'}}}")
                
                response = requests.post(
                    self.image_url,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=120
                )
                
                print(f"[Image {i+1}/{len(prompts)}] Response status: {response.status_code}")
                print(f"[Image {i+1}/{len(prompts)}] Response headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"[Image {i+1}/{len(prompts)}] Success response: {json.dumps(result, indent=2)[:300]}...")
                    
                    if "data" in result and "image_urls" in result["data"] and len(result["data"]["image_urls"]) > 0:
                        image_url = result["data"]["image_urls"][0]
                        
                        # 이미지 다운로드
                        img_response = requests.get(image_url, timeout=60)
                        if img_response.status_code == 200:
                            filename = f"step_{i+1}_image.jpg"
                            filepath = os.path.join(session_dir, filename)
                            
                            with open(filepath, "wb") as f:
                                f.write(img_response.content)
                            
                            generated_paths.append(filepath)
                            print(f"[Image {i+1}/{len(prompts)}] ✓ Successfully saved: {filename}")
                        else:
                            print(f"[Image {i+1}/{len(prompts)}] ❌ Failed to download image: {img_response.status_code}")
                    else:
                        print(f"[Image {i+1}/{len(prompts)}] ❌ No image URLs in response")
                        print(f"Response structure: {list(result.keys()) if isinstance(result, dict) else type(result)}")
                        if "data" in result:
                            print(f"Data structure: {list(result['data'].keys()) if isinstance(result['data'], dict) else type(result['data'])}")
                else:
                    print(f"[Image {i+1}/{len(prompts)}] ❌ API error: {response.status_code}")
                    print(f"Response: {response.text[:200]}...")
                    print(f"Request URL: {self.image_url}")
                    print(f"Request headers: {self._get_headers()}")
                    print(f"Request payload keys: {list(payload.keys())}")
                
                # API 레이트 리미트 방지
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"[Image {i+1}/{len(prompts)}] ❌ Error: {e}")
                continue
        
        print(f"✅ Generated {len(generated_paths)}/{len(prompts)} images successfully")
        return generated_paths
    
    async def generate_video_from_image_and_prompt(self, image_path: str, video_prompt: str, output_dir: str = "downloads/videos") -> Optional[str]:
        """
        4단계: 선택된 이미지와 비디오 프롬프트로 비디오 생성 (S2V-01 캐릭터 일관성 모델)
        
        Args:
            image_path: 3단계에서 선택된 이미지 경로
            video_prompt: 3단계에서 생성된 최적화된 비디오 프롬프트
            output_dir: 비디오 저장 디렉토리
            
        Returns:
            Generated video file path or None if failed
        """
        
        try:
            print(f"🎬 Generating CHARACTER CONSISTENT video from selected image...")
            print(f"📝 Video prompt: {video_prompt}")
            print(f"🖼️ Image path: {image_path}")
            
            # 이미지를 base64로 인코딩
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 캐릭터 일관성을 위한 프롬프트 최적화
            enhanced_prompt = self._enhance_prompt_for_character_consistency(video_prompt)
            
            # 캐릭터 일관성 설정을 위한 payload
            payload = {
                "model": "S2V-01",  # 캐릭터 일관성 전문 모델
                "prompt": enhanced_prompt,   # 캐릭터 일관성 프롬프트
                "first_frame_image": f"data:image/jpeg;base64,{base64_image}",
                "prompt_optimizer": True,    # API 최적화 활성화
                "fps": 30                    # 30fps로 설정
            }
            
            print(f"📋 CHARACTER CONSISTENCY Payload:")
            print(f"   Model: {payload['model']} (캐릭터 일관성 전문)")
            print(f"   Prompt optimizer: {payload['prompt_optimizer']}")
            print(f"   Frame Rate: {payload['fps']} fps")
            print(f"   Enhanced prompt: {enhanced_prompt[:100]}...")
            print(f"📏 Image size: {len(base64_image)} chars (base64)")
            
            # 1단계: 비디오 생성 작업 생성
            response = requests.post(
                self.video_url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            
            print(f"Video generation request status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                task_id = result.get("task_id")
                
                if task_id:
                    print(f"✅ CHARACTER CONSISTENT video generation task created: {task_id}")
                    
                    # 2단계: 작업 완료까지 폴링
                    task_result = await self._poll_task_status(task_id, max_wait_time=900)  # 15분 대기
                    
                    if task_result and task_result.get("status") == "Success":
                        file_id = task_result.get("file_id")
                        
                        if file_id:
                            print(f"📥 Downloading CHARACTER CONSISTENT video with file_id: {file_id}")
                            # 3단계: 완성된 비디오 다운로드
                            video_path = await self._download_video_by_file_id(file_id, output_dir)
                            return video_path
                        else:
                            print(f"❌ No file_id in successful task result")
                            print(f"Task result: {task_result}")
                    else:
                        print(f"❌ Task failed or timed out")
                        if task_result:
                            print(f"Task result: {task_result}")
                else:
                    print(f"❌ No task_id in response")
                    print(f"Full response: {result}")
            else:
                print(f"❌ Video generation request failed: {response.status_code}")
                print(f"Error response: {response.text}")
                
                # API 에러 분석
                try:
                    error_data = response.json()
                    if "base_resp" in error_data:
                        error_msg = error_data["base_resp"].get("status_msg", "Unknown error")
                        print(f"API Error Message: {error_msg}")
                except:
                    pass
                
            return None
                
        except Exception as e:
            print(f"❌ Error generating video: {e}")
            return None
    
    def _enhance_prompt_for_character_consistency(self, original_prompt: str) -> str:
        """
        캐릭터 일관성을 위한 프롬프트 개선 (S2V-01 전용)
        """
        # 캐릭터 일관성 키워드 확인
        consistency_keywords = [
            'same character', 'consistent', 'identical', 'maintain appearance', 
            'same person', 'character consistency', 'preserve identity'
        ]
        
        has_consistency_keyword = any(keyword in original_prompt.lower() for keyword in consistency_keywords)
        
        if not has_consistency_keyword:
            # 캐릭터 일관성 키워드 추가
            consistency_enhancement = "maintaining consistent character appearance, same facial features, identical clothing"
            enhanced_prompt = f"{original_prompt}, {consistency_enhancement}"
        else:
            enhanced_prompt = original_prompt
        
        # 급격한 변화를 피하는 키워드 추가
        if 'smooth' not in enhanced_prompt.lower() and 'gentle' not in enhanced_prompt.lower():
            enhanced_prompt = f"smooth and gentle {enhanced_prompt}"
        
        return enhanced_prompt

    def _enhance_prompt_for_director(self, original_prompt: str) -> str:
        """
        화질 향상을 위한 프롬프트 개선 (I2V-01-Director 모델용)
        """
        # 이미 고품질 키워드가 있는지 확인
        quality_keywords = [
            'high quality', 'hd', '4k', '8k', 'ultra', 'cinematic', 
            'professional', 'detailed', 'sharp', 'crystal clear'
        ]
        
        has_quality_keyword = any(keyword in original_prompt.lower() for keyword in quality_keywords)
        
        if not has_quality_keyword:
            # 화질 향상 키워드 추가
            quality_enhancement = "high quality, cinematic, detailed, professional lighting"
            enhanced_prompt = f"{original_prompt}, {quality_enhancement}"
        else:
            enhanced_prompt = original_prompt
        
        # 카메라 움직임이 없으면 안정적인 움직임 추가
        camera_movements = ['[', 'pan', 'tilt', 'zoom', 'truck', 'push', 'pull']
        has_camera_movement = any(movement in enhanced_prompt.lower() for movement in camera_movements)
        
        if not has_camera_movement:
            enhanced_prompt = f"[Slow zoom in] {enhanced_prompt}"
        
        return enhanced_prompt
    
    async def generate_videos_from_images_and_prompts(self, image_paths: List[str], video_prompts: List[str], output_dir: str = "downloads/videos") -> List[str]:
        """
        여러 이미지와 프롬프트로 순서대로 비디오들 생성 (S2V-01 캐릭터 일관성 모델)
        
        Args:
            image_paths: 원본 이미지들의 경로 리스트
            video_prompts: 각 이미지에 대응하는 비디오 프롬프트 리스트
            output_dir: 비디오 저장 디렉토리
            
        Returns:
            List of generated video file paths
        """
        
        if len(image_paths) != len(video_prompts):
            print(f"❌ Image count ({len(image_paths)}) doesn't match prompt count ({len(video_prompts)})")
            return []
        
        try:
            print(f"🎬 Generating {len(image_paths)} CHARACTER CONSISTENT videos from images and prompts...")
            
            # 모든 작업을 한 번에 제출
            task_ids = []
            
            for i, (image_path, video_prompt) in enumerate(zip(image_paths, video_prompts)):
                try:
                    print(f"[Video {i+1}/{len(image_paths)}] 🚀 Submitting CHARACTER CONSISTENT generation task...")
                    print(f"  Image: {image_path}")
                    print(f"  Prompt: {video_prompt[:80]}...")
                    
                    # 이미지를 base64로 인코딩
                    with open(image_path, "rb") as image_file:
                        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                    
                    # 캐릭터 일관성을 위한 프롬프트 최적화
                    enhanced_prompt = self._enhance_prompt_for_character_consistency(video_prompt)
                    
                    # 캐릭터 일관성 설정을 위한 payload
                    payload = {
                        "model": "S2V-01",  # 캐릭터 일관성 전문 모델
                        "prompt": enhanced_prompt,   # 캐릭터 일관성 프롬프트
                        "first_frame_image": f"data:image/jpeg;base64,{base64_image}",
                        "prompt_optimizer": True,    # API 최적화 활성화
                        "fps": 30                    # 30fps로 설정
                    }
                    
                    print(f"  📋 CHARACTER CONSISTENCY Settings:")
                    print(f"     Model: S2V-01 (캐릭터 일관성 전문)")
                    print(f"     Frame Rate: 30 fps")
                    print(f"     Enhanced prompt: {enhanced_prompt[:60]}...")
                    print(f"     Image size: {len(base64_image)} chars (base64)")
                    
                    response = requests.post(
                        self.video_url,
                        headers=self._get_headers(),
                        json=payload,
                        timeout=30
                    )
                    
                    print(f"[Video {i+1}/{len(image_paths)}] Response status: {response.status_code}")
                    print(f"[Video {i+1}/{len(image_paths)}] Response: {response.text}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        task_id = result.get("task_id")
                        
                        if task_id:
                            task_ids.append((task_id, i+1, image_path))
                            print(f"[Video {i+1}/{len(image_paths)}] ✅ CHARACTER CONSISTENT Task created: {task_id}")
                        else:
                            print(f"[Video {i+1}/{len(image_paths)}] ❌ No task_id in response")
                            print(f"Full response: {result}")
                    else:
                        print(f"[Video {i+1}/{len(image_paths)}] ❌ Task creation failed: {response.status_code}")
                        print(f"Error response: {response.text}")
                        
                        # API 에러 분석
                        try:
                            error_data = response.json()
                            if "base_resp" in error_data:
                                error_msg = error_data["base_resp"].get("status_msg", "Unknown error")
                                print(f"API Error Message: {error_msg}")
                        except:
                            pass
                    
                    # API 레이트 리미트 방지
                    if i < len(image_paths) - 1:
                        await asyncio.sleep(5)  # 5초 대기
                        
                except Exception as e:
                    print(f"[Video {i+1}/{len(image_paths)}] ❌ Error submitting task: {e}")
                    continue
            
            print(f"📝 Submitted {len(task_ids)}/{len(image_paths)} CHARACTER CONSISTENT video generation tasks")
            
            if not task_ids:
                print(f"❌ No tasks were successfully submitted")
                return []
            
            # 모든 작업이 완료될 때까지 폴링
            generated_videos = []
            
            for task_id, video_index, image_path in task_ids:
                try:
                    print(f"[Video {video_index}] ⏳ Waiting for CHARACTER CONSISTENT task {task_id} to complete...")
                    
                    # 캐릭터 일관성 비디오 대기
                    task_result = await self._poll_task_status(task_id, max_wait_time=900)  # 15분 대기
                    
                    if task_result and task_result.get("status") == "Success":
                        file_id = task_result.get("file_id")
                        
                        if file_id:
                            print(f"[Video {video_index}] 📥 Downloading CHARACTER CONSISTENT video with file_id: {file_id}")
                            video_path = await self._download_video_by_file_id(file_id, output_dir)
                            
                            if video_path:
                                generated_videos.append(video_path)
                                print(f"[Video {video_index}] ✅ CHARACTER CONSISTENT video successfully generated and downloaded")
                            else:
                                print(f"[Video {video_index}] ❌ Failed to download video")
                        else:
                            print(f"[Video {video_index}] ❌ No file_id in successful task")
                            print(f"Task result: {task_result}")
                    else:
                        print(f"[Video {video_index}] ❌ Task failed or timed out")
                        if task_result:
                            print(f"Task result: {task_result}")
                        
                except Exception as e:
                    print(f"[Video {video_index}] ❌ Error processing task: {e}")
                    continue
            
            print(f"✅ Generated {len(generated_videos)}/{len(image_paths)} CHARACTER CONSISTENT videos successfully")
            return generated_videos
                
        except Exception as e:
            print(f"❌ Error generating videos: {e}")
            return []

    # 🆕 1단계: 10단계 장면별 프롬프트 생성
    def generate_10_step_scene_prompts(self, main_description: str, reference_image_path: str = None, style_options: Dict = None) -> List[str]:
        """
        메인 설명을 10단계 장면으로 나누어 미드저니 스타일 프롬프트 생성
        
        Args:
            main_description: 사용자가 설명한 메인 내용
            reference_image_path: 실제 강아지 사진 경로 (특징 분석용)
            style_options: 스타일 옵션 (캐릭터 일관성, 조명 등)
            
        Returns:
            List of 10 Midjourney-style scene prompts based on actual dog
        """
        
        print(f"🎬 Generating 10-step Midjourney scene prompts for: {main_description}")
        if reference_image_path:
            print(f"📷 Using reference dog photo: {reference_image_path}")
        
        # 🆕 OpenAI 서비스를 사용해서 실제 강아지 사진 기반 미드저니 스타일 10단계 장면 생성
        try:
            from services.openai_service import OpenAIService
            openai_service = OpenAIService()
            
            # OpenAI로 10단계 미드저니 프롬프트 생성 (실제 강아지 사진 분석 포함)
            import asyncio
            if asyncio.get_event_loop().is_running():
                # 이미 이벤트 루프가 실행 중인 경우
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, 
                        openai_service.generate_10_step_scene_descriptions(main_description, reference_image_path)
                    )
                    midjourney_prompts = future.result()
            else:
                # 새로운 이벤트 루프 생성
                midjourney_prompts = asyncio.run(openai_service.generate_10_step_scene_descriptions(main_description, reference_image_path))
            
            print(f"✅ Generated {len(midjourney_prompts)} Midjourney-style prompts based on actual dog photo")
            
            # 스타일 옵션이 제공되면 추가 처리
            if style_options:
                enhanced_prompts = []
                for i, prompt in enumerate(midjourney_prompts):
                    # 추가 스타일 옵션 적용
                    enhanced_prompt = self._apply_additional_style_options(prompt, style_options)
                    enhanced_prompts.append(enhanced_prompt)
                    print(f"Scene {i+1}: {enhanced_prompt[:100]}...")
                return enhanced_prompts
            else:
                # 기본 미드저니 프롬프트 반환
                for i, prompt in enumerate(midjourney_prompts):
                    print(f"Scene {i+1}: {prompt[:100]}...")
                return midjourney_prompts
            
        except Exception as e:
            print(f"⚠️ OpenAI Midjourney prompt generation failed: {e}")
            print("🔄 Using fallback Midjourney prompts...")
            return self._generate_fallback_midjourney_prompts(main_description)

    def _apply_additional_style_options(self, prompt: str, style_options: Dict) -> str:
        """추가 스타일 옵션을 미드저니 프롬프트에 적용"""
        
        # 기존 스타일 매개변수 제거 (다시 추가하기 위해)
        prompt = prompt.replace("--style raw", "").replace("--style photographic", "")
        prompt = prompt.replace("--v 6", "").replace("--ar 9:16", "")
        prompt = prompt.replace("consistent lighting", "").strip()
        
        # 새로운 스타일 옵션 구성
        style_parts = ["--style raw"]  # 기본 현실적 스타일
        
        # 캐릭터 일관성 옵션
        if style_options.get("character_consistency", True):
            style_parts.append("--style photographic")
        
        # 조명 일관성 옵션
        if style_options.get("consistent_lighting", True):
            style_parts.append("consistent lighting")
        
        # 기본 매개변수
        style_parts.extend(["--v 6", "--ar 9:16"])
        
        # 프롬프트에 스타일 추가
        enhanced_prompt = f"{prompt} {' '.join(style_parts)}"
        
        return enhanced_prompt

    def _generate_fallback_midjourney_prompts(self, main_description: str) -> List[str]:
        """미드저니 프롬프트 생성 실패 시 폴백 프롬프트들"""
        base_style = "--style raw --style photographic --v 6 --ar 9:16 consistent lighting"
        
        if "강아지" in main_description and ("유치원" in main_description or "놀이" in main_description):
            return [
                f"A cute puppy getting ready at home, looking excited with bright eyes and wagging tail. {base_style}",
                f"The same puppy walking towards a colorful kindergarten building with other puppies visible in the background. {base_style}",
                f"The puppy arriving at the kindergarten entrance, meeting friendly staff and other puppies for the first time. {base_style}",
                f"The puppy cautiously exploring the kindergarten playground, sniffing around with curiosity and wonder. {base_style}",
                f"The puppy starting to play with colorful toys scattered around the kindergarten play area. {base_style}",
                f"The puppy meeting and greeting other puppies, beginning to form new friendships through gentle interactions. {base_style}",
                f"The puppy actively playing with other puppies, running around together in the safe kindergarten environment. {base_style}",
                f"The puppy engaged in group play activities, showing joy and excitement while interacting with multiple puppies. {base_style}",
                f"The puppy and friends playing their favorite games together, showing pure happiness and playful energy. {base_style}",
                f"The tired but happy puppy resting after playtime, surrounded by new friends in a peaceful moment. {base_style}"
            ]
        else:
            return [
                f"A character preparing for an important journey or activity, showing determination and readiness. {base_style}",
                f"The same character taking the first steps toward their goal, moving with purpose and confidence. {base_style}",
                f"The character arriving at their destination, taking in the new environment with curiosity. {base_style}",
                f"The character beginning their main activity, showing focus and initial engagement. {base_style}",
                f"The character becoming more involved in the activity, showing growing enthusiasm and skill. {base_style}",
                f"The character interacting with others or elements in the environment, building connections. {base_style}",
                f"The character reaching a peak moment of activity, showing intense focus and energy. {base_style}",
                f"The character experiencing a breakthrough or special moment, radiating joy and accomplishment. {base_style}",
                f"The character completing their main activity with satisfaction and sense of achievement. {base_style}",
                f"The character reflecting on the experience, showing contentment and peaceful completion. {base_style}"
            ]

    # 🆕 2단계: 이미지 생성 + 재생성 옵션
    async def generate_scene_images_with_regeneration(self, scene_prompts: List[str], reference_image_path: str = None, output_dir: str = "downloads/scene_images") -> List[Dict]:
        """
        장면별 이미지 생성 (재생성 옵션 포함)
        
        Args:
            scene_prompts: 10개 장면 프롬프트
            reference_image_path: 참고 이미지 (선택사항)
            output_dir: 저장 디렉토리
            
        Returns:
            List of image info with regeneration options
        """
        
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = os.path.join(output_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        print(f"🎨 Generating {len(scene_prompts)} scene images...")
        print(f"📁 Images will be saved to: {session_dir}/")
        
        # 참고 이미지 처리
        reference_base64 = None
        if reference_image_path and os.path.exists(reference_image_path):
            try:
                with open(reference_image_path, "rb") as image_file:
                    reference_base64 = base64.b64encode(image_file.read()).decode('utf-8')
                print(f"📷 Reference image loaded: {reference_image_path}")
            except Exception as e:
                print(f"⚠️ Error loading reference image: {e}")
        
        generated_images = []
        
        for i, prompt in enumerate(scene_prompts):
            try:
                print(f"[Scene {i+1}/10] 🚀 Generating image...")
                print(f"  Prompt: {prompt[:100]}...")
                
                # 이미지 생성 payload
                payload = {
                    "model": "image-01",
                    "prompt": prompt,
                    "n": 1
                }
                
                # 참고 이미지 추가 (있을 경우)
                if reference_base64:
                    payload["subject_reference"] = [
                        {
                            "type": "person",  # character → person으로 변경 (더 현실적)
                            "image_file": f"data:image/jpeg;base64,{reference_base64}"
                        }
                    ]
                    print(f"[Scene {i+1}/10] 📷 Reference image included (size: {len(reference_base64)} chars)")
                else:
                    print(f"[Scene {i+1}/10] ⚠️ No reference image provided")
                
                print(f"[Scene {i+1}/10] 📤 Payload: {{'model': '{payload['model']}', 'prompt': '{prompt[:50]}...', 'subject_reference': {'YES' if 'subject_reference' in payload else 'NO'}}}")
                
                response = requests.post(
                    self.image_url,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=120
                )
                
                print(f"[Scene {i+1}/10] Response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"[Scene {i+1}/10] Full response: {result}")
                    
                    # 안전한 응답 체크
                    data = result.get("data")
                    if data is not None and isinstance(data, dict):
                        image_urls = data.get("image_urls")
                        if image_urls is not None and isinstance(image_urls, list) and len(image_urls) > 0:
                            image_url = image_urls[0]
                            
                            # 이미지 다운로드
                            img_response = requests.get(image_url, timeout=60)
                            if img_response.status_code == 200:
                                filename = f"scene_{i+1:02d}_image.jpg"
                                filepath = os.path.join(session_dir, filename)
                                
                                with open(filepath, "wb") as f:
                                    f.write(img_response.content)
                                
                                # 이미지 정보 저장
                                image_info = {
                                    "scene_number": i + 1,
                                    "prompt": prompt,
                                    "filepath": filepath,
                                    "filename": filename,
                                    "status": "success",
                                    "needs_regeneration": False  # 사용자가 나중에 설정
                                }
                                
                                generated_images.append(image_info)
                                print(f"[Scene {i+1}/10] ✅ Successfully saved: {filename}")
                            else:
                                print(f"[Scene {i+1}/10] ❌ Failed to download image: {img_response.status_code}")
                                # 실패한 경우도 기록
                                image_info = {
                                    "scene_number": i + 1,
                                    "prompt": prompt,
                                    "filepath": None,
                                    "filename": None,
                                    "status": "failed",
                                    "needs_regeneration": True
                                }
                                generated_images.append(image_info)
                        else:
                            print(f"[Scene {i+1}/10] ❌ No image URLs in response")
                            print(f"[Scene {i+1}/10] image_urls: {image_urls}")
                            print(f"[Scene {i+1}/10] data structure: {data}")
                            image_info = {
                                "scene_number": i + 1,
                                "prompt": prompt,
                                "filepath": None,
                                "filename": None,
                                "status": "failed",
                                "needs_regeneration": True
                            }
                            generated_images.append(image_info)
                    else:
                        print(f"[Scene {i+1}/10] ❌ No data field in response or data is None")
                        print(f"[Scene {i+1}/10] result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                        print(f"[Scene {i+1}/10] data value: {data}")
                        image_info = {
                            "scene_number": i + 1,
                            "prompt": prompt,
                            "filepath": None,
                            "filename": None,
                            "status": "failed",
                            "needs_regeneration": True
                        }
                        generated_images.append(image_info)
                else:
                    print(f"[Scene {i+1}/10] ❌ API error: {response.status_code}")
                    print(f"[Scene {i+1}/10] Error response: {response.text}")
                    image_info = {
                        "scene_number": i + 1,
                        "prompt": prompt,
                        "filepath": None,
                        "filename": None,
                        "status": "failed",
                        "needs_regeneration": True
                    }
                    generated_images.append(image_info)
                
                # API 레이트 리미트 방지
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"[Scene {i+1}/10] ❌ Error: {e}")
                image_info = {
                    "scene_number": i + 1,
                    "prompt": prompt,
                    "filepath": None,
                    "filename": None,
                    "status": "error",
                    "error": str(e),
                    "needs_regeneration": True
                }
                generated_images.append(image_info)
                continue
        
        success_count = len([img for img in generated_images if img["status"] == "success"])
        print(f"✅ Generated {success_count}/10 scene images successfully")
        
        return generated_images

    # 🆕 2-1단계: 개별 이미지 재생성
    async def regenerate_scene_image(self, scene_number: int, prompt: str = None, original_prompt: str = None, reference_image_path: str = None, output_dir: str = "downloads/scene_images") -> Dict:
        """
        특정 장면의 이미지 재생성
        
        Args:
            scene_number: 장면 번호 (1-10)
            prompt: 새로운 프롬프트 (선택사항, None이면 original_prompt 사용)
            original_prompt: 원본 프롬프트
            reference_image_path: 참고 이미지
            output_dir: 저장 디렉토리
            
        Returns:
            Regenerated image info
        """
        
        final_prompt = prompt if prompt else original_prompt
        
        print(f"🔄 Regenerating Scene {scene_number} image...")
        print(f"📝 Using prompt: {final_prompt[:100]}...")
        
        # 참고 이미지 처리
        reference_base64 = None
        if reference_image_path and os.path.exists(reference_image_path):
            try:
                with open(reference_image_path, "rb") as image_file:
                    reference_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            except Exception as e:
                print(f"⚠️ Error loading reference image: {e}")
        
        try:
            # 이미지 생성 payload
            payload = {
                "model": "image-01",
                "prompt": final_prompt,
                "n": 1
            }
            
            # 참고 이미지 추가
            if reference_base64:
                payload["subject_reference"] = [
                    {
                        "type": "person",  # character → person으로 변경 (더 현실적)
                        "image_file": f"data:image/jpeg;base64,{reference_base64}"
                    }
                ]
                print(f"📷 Reference image included for regeneration")
            
            print(f"📤 Regeneration payload: {{'model': '{payload['model']}', 'prompt': '{final_prompt[:50]}...', 'subject_reference': {'YES' if 'subject_reference' in payload else 'NO'}}}")
            
            response = requests.post(
                self.image_url,
                headers=self._get_headers(),
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if "data" in result and "image_urls" in result["data"] and len(result["data"]["image_urls"]) > 0:
                    image_url = result["data"]["image_urls"][0]
                    
                    # 이미지 다운로드
                    img_response = requests.get(image_url, timeout=60)
                    if img_response.status_code == 200:
                        timestamp = datetime.now().strftime("%H%M%S")
                        filename = f"scene_{scene_number:02d}_regenerated_{timestamp}.jpg"
                        
                        # 최신 세션 디렉토리 찾기
                        session_dirs = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d))]
                        if session_dirs:
                            latest_session = max(session_dirs)
                            filepath = os.path.join(output_dir, latest_session, filename)
                        else:
                            os.makedirs(output_dir, exist_ok=True)
                            filepath = os.path.join(output_dir, filename)
                        
                        with open(filepath, "wb") as f:
                            f.write(img_response.content)
                        
                        return {
                            "scene_number": scene_number,
                            "prompt": final_prompt,
                            "filepath": filepath,
                            "filename": filename,
                            "status": "success",
                            "regenerated": True
                        }
            
            return {
                "scene_number": scene_number,
                "prompt": final_prompt,
                "filepath": None,
                "filename": None,
                "status": "failed",
                "regenerated": True
            }
            
        except Exception as e:
            return {
                "scene_number": scene_number,
                "prompt": final_prompt,
                "filepath": None,
                "filename": None,
                "status": "error",
                "error": str(e),
                "regenerated": True
            }

    # 🆕 3단계: 영상용 프롬프트 생성
    def generate_video_prompts_from_scenes(self, scene_images: List[Dict]) -> List[str]:
        """
        장면 이미지들을 기반으로 영상용 프롬프트 생성
        
        Args:
            scene_images: 장면 이미지 정보 리스트
            
        Returns:
            List of video prompts for each scene
        """
        
        print(f"🎬 Generating video prompts for {len(scene_images)} scenes...")
        
        video_prompts = []
        
        # 🆕 자연스러운 동작 중심의 템플릿 (카메라 용어 제거)
        action_templates = [
            "캐릭터가 천천히 준비하며 주변을 둘러보는 모습",
            "캐릭터의 표정 변화와 자연스러운 움직임",
            "캐릭터가 환경을 탐색하며 천천히 이동하는 모습", 
            "캐릭터가 활동을 시작하며 움직이기 시작하는 장면",
            "캐릭터가 활동에 몰입하며 즐거워하는 모습",
            "캐릭터가 상황에 반응하며 자연스럽게 행동하는 장면",
            "캐릭터가 중요한 순간에 집중하는 모습",
            "캐릭터가 적극적으로 행동하며 움직이는 장면", 
            "캐릭터가 절정의 순간을 경험하는 모습",
            "캐릭터가 마무리하며 만족스러워하는 장면"
        ]
        
        for i, scene_info in enumerate(scene_images):
            if scene_info["status"] == "success":
                # 자연스러운 동작 템플릿
                base_action = action_templates[i] if i < len(action_templates) else "캐릭터가 자연스럽게 움직이는 모습"
                
                # S2V-01에 최적화된 영상 프롬프트 생성
                video_prompt = f"Scene {i+1}: {base_action}. 캐릭터의 일관된 외모 유지. 부드럽고 자연스러운 움직임과 조명."
                
                video_prompts.append(video_prompt)
                print(f"📝 Scene {i+1} video prompt: {video_prompt[:80]}...")
            else:
                # 실패한 장면은 빈 프롬프트
                video_prompts.append("")
                print(f"⚠️ Scene {i+1}: Skipping due to image generation failure")
        
        return video_prompts 