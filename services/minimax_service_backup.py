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
        
        # API 키와 Group ID 확인
        if not self.api_key:
            print("WARNING: MINIMAX_API_KEY not set in environment variables")
        if not self.group_id:
            print("WARNING: MINIMAX_GROUP_ID not set in environment variables - required for file retrieval")
            
        self.base_url = "https://api.minimaxi.chat/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.image_dir = os.path.abspath("downloads/minimax_images")
        self.video_dir = os.path.abspath("downloads/videos")
        self.checkpoint_dir = os.path.abspath("downloads/checkpoints")
        os.makedirs(self.image_dir, exist_ok=True)
        os.makedirs(self.video_dir, exist_ok=True)
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        
    def _get_checkpoint_path(self, session_id: str) -> str:
        """체크포인트 파일 경로 반환"""
        return os.path.join(self.checkpoint_dir, f"checkpoint_{session_id}.json")
    
    def _save_checkpoint(self, session_id: str, checkpoint_data: Dict):
        """진행 상황을 체크포인트 파일에 저장"""
        checkpoint_path = self._get_checkpoint_path(session_id)
        try:
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Checkpoint saved: {os.path.basename(checkpoint_path)}")
        except Exception as e:
            print(f"⚠️  Failed to save checkpoint: {e}")
    
    def _load_checkpoint(self, session_id: str) -> Dict:
        """체크포인트 파일에서 진행 상황 로드"""
        checkpoint_path = self._get_checkpoint_path(session_id)
        if os.path.exists(checkpoint_path):
            try:
                with open(checkpoint_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"📂 Checkpoint loaded: {os.path.basename(checkpoint_path)}")
                return data
            except Exception as e:
                print(f"⚠️  Failed to load checkpoint: {e}")
        return {}
    
    def _clear_checkpoint(self, session_id: str):
        """완료 후 체크포인트 파일 삭제"""
        checkpoint_path = self._get_checkpoint_path(session_id)
        try:
            if os.path.exists(checkpoint_path):
                os.remove(checkpoint_path)
                print(f"🗑️  Checkpoint cleared: {os.path.basename(checkpoint_path)}")
        except Exception as e:
            print(f"⚠️  Failed to clear checkpoint: {e}")
    
    def _create_session_id(self) -> str:
        """고유한 세션 ID 생성"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def list_checkpoints(self) -> List[Dict]:
        """저장된 체크포인트 목록 반환"""
        checkpoints = []
        try:
            for filename in os.listdir(self.checkpoint_dir):
                if filename.startswith("checkpoint_") and filename.endswith(".json"):
                    checkpoint_path = os.path.join(self.checkpoint_dir, filename)
                    try:
                        with open(checkpoint_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        session_id = filename.replace("checkpoint_", "").replace(".json", "")
                        checkpoint_info = {
                            'session_id': session_id,
                            'phase': data.get('phase', 'unknown'),
                            'completed': data.get('completed', False),
                            'total_prompts': data.get('total_prompts', 0),
                            'total_images': data.get('total_images', 0),
                            'completed_images': len(data.get('completed_images', [])),
                            'completed_videos': len(data.get('completed_videos', [])),
                            'last_update': data.get('last_update'),
                            'failed_at': data.get('failed_at'),
                            'start_time': data.get('start_time')
                        }
                        checkpoints.append(checkpoint_info)
                    except Exception as e:
                        print(f"⚠️  Error reading checkpoint {filename}: {e}")
            
            # 최신 순으로 정렬
            checkpoints.sort(key=lambda x: x.get('last_update', 0), reverse=True)
            
        except Exception as e:
            print(f"⚠️  Error listing checkpoints: {e}")
        
        return checkpoints
    
    def print_checkpoints(self):
        """체크포인트 목록을 보기 좋게 출력"""
        checkpoints = self.list_checkpoints()
        
        if not checkpoints:
            print("📝 No checkpoints found.")
            return
        
        print(f"\n{'='*80}")
        print("📝 AVAILABLE CHECKPOINTS")
        print(f"{'='*80}")
        
        for checkpoint in checkpoints:
            session_id = checkpoint['session_id']
            phase = checkpoint['phase']
            completed = checkpoint['completed']
            
            print(f"\n🆔 Session ID: {session_id}")
            print(f"📋 Phase: {phase}")
            print(f"✅ Completed: {'Yes' if completed else 'No'}")
            
            if phase == 'image_generation':
                total = checkpoint['total_prompts']
                done = checkpoint['completed_images']
                print(f"🖼️  Images: {done}/{total}")
            elif phase == 'video_generation':
                total = checkpoint['total_images']
                done = checkpoint['completed_videos']
                print(f"🎬 Videos: {done}/{total}")
            
            if checkpoint.get('failed_at'):
                failed_info = checkpoint['failed_at']
                print(f"❌ Failed at index {failed_info.get('index', 'unknown')}: {failed_info.get('error', 'Unknown error')}")
            
            if checkpoint.get('last_update'):
                last_update = datetime.fromtimestamp(checkpoint['last_update'])
                print(f"🕐 Last update: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
            
            print("-" * 50)
        
        print(f"\n💡 To resume from a checkpoint, use: session_id='SESSION_ID'")
        print(f"💡 To clear a checkpoint, use: clear_checkpoint('SESSION_ID')")
        
    def clear_checkpoint(self, session_id: str):
        """특정 체크포인트 삭제"""
        self._clear_checkpoint(session_id)
        
    def clear_all_checkpoints(self):
        """모든 체크포인트 삭제"""
        try:
            checkpoints = self.list_checkpoints()
            for checkpoint in checkpoints:
                self._clear_checkpoint(checkpoint['session_id'])
            print(f"🗑️  Cleared {len(checkpoints)} checkpoint(s)")
        except Exception as e:
            print(f"⚠️  Error clearing checkpoints: {e}")
        
    async def generate_images(self, prompts: List[str], session_id: str = None) -> List[str]:
        """프롬프트 리스트를 받아 이미지 생성 - 체크포인트 지원"""
        if not self.api_key:
            raise RuntimeError("MINIMAX_API_KEY not set in .env file")
            
        # 세션 ID 생성 또는 사용
        if session_id is None:
            session_id = self._create_session_id()
        
        # 체크포인트 로드
        checkpoint = self._load_checkpoint(session_id)
        
        total_start_time = time.time()
        
        print(f"\n{'='*60}")
        print(f"Starting BATCH image generation for {len(prompts)} prompts")
        print(f"Session ID: {session_id}")
        print(f"Processing 2 images at a time (safer for API limits)")
        print(f"⚠️  Process will STOP on first failure")
        print(f"🔄 Resume from checkpoint if available")
        print(f"{'='*60}")
        
        print(f"\n{'='*60}")
        print(f"Starting SEQUENTIAL image generation for {len(prompts)} prompts")
        print(f"Session ID: {session_id}")
        print(f"Processing 1 image at a time (safest for API limits)")
        print(f"⚠️  Process will STOP on first failure")
        print(f"🔄 Resume from checkpoint if available")
        print(f"{'='*60}")
        
        print(f"\n{'='*60}")
        print(f"Starting SEQUENTIAL image generation for {len(prompts)} prompts")
        print(f"Session ID: {session_id}")
        print(f"Processing 1 image at a time (safest for API limits)")
        print(f"⚠️  Process will STOP on first failure")
        print(f"🔄 Resume from checkpoint if available")
        print(f"{'='*60}")
        
        print(f"\n{'='*60}")
        print(f"Starting BATCH image generation for {len(prompts)} prompts")
        print(f"Session ID: {session_id}")
        print(f"Processing 3 images at a time (optimized batch size)")
        print(f"⚠️  Process will STOP on first failure")
        print(f"🔄 Resume from checkpoint if available")
        print(f"{'='*60}")
        
        # 체크포인트에서 이미 완료된 이미지들 확인
        completed_images = checkpoint.get('completed_images', [])
        generated_images = checkpoint.get('generated_images', [])
        
        # 완료된 개수 확인
        start_index = len(completed_images)
        if start_index > 0:
            print(f"\n🔄 RESUMING FROM CHECKPOINT:")
            print(f"   Already completed: {start_index}/{len(prompts)} images")
            print(f"   Starting from image {start_index + 1}")
        
        # 체크포인트 초기화 (첫 시작인 경우)
        if 'session_id' not in checkpoint:
            checkpoint = {
                'session_id': session_id,
                'total_prompts': len(prompts),
                'prompts': prompts,
                'completed_images': [],
                'generated_images': [],
                'start_time': total_start_time,
                'phase': 'image_generation'
            }
            self._save_checkpoint(session_id, checkpoint)
        
        # 남은 프롬프트들만 처리
        remaining_prompts = prompts[start_index:]
        if not remaining_prompts:
            print(f"✅ All images already completed!")
            return generated_images
        
        # 3개씩 배치 처리 (더 효율적)
        batch_size = 3
        for batch_start in range(0, len(remaining_prompts), batch_size):
            batch_end = min(batch_start + batch_size, len(remaining_prompts))
            batch_prompts = remaining_prompts[batch_start:batch_end]
            
            actual_start = start_index + batch_start
            actual_end = start_index + batch_end
            
            print(f"\n🔄 Processing batch {batch_start//batch_size + 1}/{(len(remaining_prompts) + batch_size - 1)//batch_size}")
            print(f"   Images {actual_start + 1}-{actual_end}")
            
            # 배치 실행
            batch_results = []  # 초기화 추가
            
            async def generate_single_image(index: int, prompt: str):
                real_index = actual_start + index
                print(f"[Image {real_index+1}/{len(prompts)}] 🚀 Starting generation...")
                
                async with aiohttp.ClientSession() as session:
                    try:
                        image_path = await self._generate_single_image(session, prompt, real_index, session_id)
                        if image_path:
                            print(f"[Image {real_index+1}/{len(prompts)}] ✓ Successfully completed")
                            return image_path
                        else:
                            # 실패 시 예외 발생
                            error_msg = f"Failed to generate image {real_index+1}"
                            print(f"[Image {real_index+1}/{len(prompts)}] ❌ {error_msg}")
                            raise RuntimeError(error_msg)
                    except Exception as e:
                        error_msg = f"Error generating image {real_index+1}: {e}"
                        print(f"[Image {real_index+1}/{len(prompts)}] ❌ {error_msg}")
                        raise RuntimeError(error_msg)
            
            tasks = [generate_single_image(i, prompt) for i, prompt in enumerate(batch_prompts)]
            batch_results = await asyncio.gather(*tasks)  # return_exceptions=True 제거
            
            try:
                # 성공한 결과들 추가 및 체크포인트 업데이트
                for i, result in enumerate(batch_results):
                    real_index = actual_start + i
                    generated_images.append(result)
                    completed_images.append(real_index)
                    
                    # 각 이미지 완료 후 체크포인트 저장
                    checkpoint['completed_images'] = completed_images
                    checkpoint['generated_images'] = generated_images
                    checkpoint['last_completed_index'] = real_index
                    checkpoint['last_update'] = time.time()
                    self._save_checkpoint(session_id, checkpoint)
                    
            except Exception as e:
                # 실패 시 체크포인트 저장 후 중단
                failed_index = actual_start + len(batch_results)  # 이제 batch_results가 항상 정의됨
                checkpoint['failed_at'] = {
                    'index': failed_index,
                    'error': str(e),
                    'timestamp': time.time()
                }
                self._save_checkpoint(session_id, checkpoint)
                
                print(f"\n{'='*60}")
                print(f"❌ IMAGE GENERATION FAILED - STOPPING PROCESS")
                print(f"Error: {e}")
                print(f"Completed images: {len(completed_images)}/{len(prompts)}")
                print(f"💾 Progress saved to checkpoint: {session_id}")
                print(f"🔄 To resume, use the same session_id: {session_id}")
                print(f"{'='*60}")
                raise RuntimeError(f"Image generation failed: {e}")
            
            # 배치 간 대기 (API 제한 방지)
            if actual_end < len(prompts):
                print(f"⏳ Waiting 5 seconds before next batch...")
                await asyncio.sleep(5)
        
            # 배치 간 대기 (API 제한 방지)
            if actual_end < len(prompts):
                print(f"⏳ Waiting 10 seconds before next image...")
                await asyncio.sleep(10)
                
            # 배치 간 대기 (API 제한 방지)
            if actual_end < len(prompts):
                print(f"⏳ Waiting 8 seconds before next batch...")
                await asyncio.sleep(8)
        
        total_time = int(time.time() - total_start_time)
        success_count = len(generated_images)
        
        # 완료 체크포인트 업데이트
        checkpoint['completed'] = True
        checkpoint['completion_time'] = time.time()
        checkpoint['total_time'] = total_time
        self._save_checkpoint(session_id, checkpoint)
        
        print(f"\n{'='*60}")
        print(f"✅ ALL IMAGES GENERATED SUCCESSFULLY!")
        print(f"  Session ID: {session_id}")
        print(f"  Total time: {total_time // 60}m {total_time % 60}s")
        print(f"  Success rate: {success_count}/{len(prompts)}")
        print(f"{'='*60}\n")
                
        return generated_images
        
    async def _generate_single_image(self, session: aiohttp.ClientSession, prompt: str, index: int, session_id: str = None) -> str:
        """단일 프롬프트로 이미지 생성"""
        try:
            # 강화된 실사 스타일 키워드 + 더욱 강력한 3분할 방지 키워드 추가
            realistic_keywords = ", ultra-realistic photograph, DSLR camera quality, sharp focus, natural textures, professional studio lighting, photojournalism style, documentary photography, high resolution, detailed fur texture, Canon EOS R5, 85mm lens, natural window lighting, NOT cartoon, NOT anime, NOT illustration, NOT drawing, NOT artistic rendering"
            anti_split_keywords = ", single scene, single image, unified composition, continuous scene, single moment in time, ONE scene only, NOT split screen, NOT multiple panels, NOT grid, NOT collage, NOT triptych, NOT diptych, NOT multiple views, NOT before and after, NOT step by step visual, NOT comparison, NOT showcase format, NOT presentation layout, NOT display montage, NO panels, NO divisions, NO separations"
            style_enhanced_prompt = f"{prompt[:1000]}{realistic_keywords}{anti_split_keywords}"
            
            print(f"\nGenerating image {index+1}/10:")
            
            # Minimax Image Generation API 엔드포인트
            url = f"{self.base_url}/image_generation"
            
            # API 문서에 맞는 올바른 payload 구조
            payload = {
                "model": "image-01",  # 올바른 이미지 생성 모델
                "prompt": style_enhanced_prompt[:1500],  # 강화된 실사 키워드 + 3분할 방지 키워드 포함
                "aspect_ratio": "9:16",  # 기본 9:16, 다른 옵션: "1:1", "4:3", "3:2", "2:3", "3:4", "16:9", "21:9"
                "response_format": "url",  # URL 형식으로 응답 (24시간 유효)
                "n": 1,  # 생성할 이미지 수 (1-9)
                "prompt_optimizer": False  # 빠른 처리를 위해 프롬프트 최적화 비활성화 (분할 방지)
            }
            
            print(f"\nGenerating image {index+1}/10:")
            print(f"  Prompt preview: {prompt[:80]}...")
            print(f"  Calling Minimax Image API...")
            
            async with session.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=150)  # 60초 타임아웃
            ) as response:
                response_text = await response.text()
                
                if response.status != 200:
                    print(f"  API Error: {response.status}")
                    print(f"  Error details: {response_text[:300]}")
                    if response.status == 401:
                        print("  Authentication failed. Please check your MINIMAX_API_KEY")
                    return ""
                    
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError:
                    print(f"  Failed to parse JSON response")
                    return ""
                
                # base_resp 체크
                if "base_resp" in result:
                    base_resp = result["base_resp"]
                    if base_resp.get("status_code") != 0:
                        print(f"  API error: {base_resp.get('status_code')} - {base_resp.get('status_msg')}")
                        return ""
                
                # 성공적인 응답 처리
                if "data" in result:
                    data = result["data"]
                    
                    # image_urls 필드로 URL이 직접 반환되는 경우
                    if "image_urls" in data and len(data["image_urls"]) > 0:
                        image_url = data["image_urls"][0]
                        return await self._download_image(session, image_url, index, session_id)
                    
                    # task_id가 반환되는 경우 (비동기 처리)
                    elif "task_id" in data:
                        print(f"  Task created: {data['task_id']}")
                        image_url = await self._wait_for_image_task(session, data["task_id"], session_id)
                        if image_url:
                            return await self._download_image(session, image_url, index, session_id)
                            
                    # task_id가 반환되는 경우 (비동기 처리)  
                    elif "task_id" in data:
                        print(f"  Task created: {data['task_id']}")
                        image_path = await self._wait_for_image_task(session, data["task_id"], session_id, index)
                        if image_path:
                            return image_path
                
                print(f"  Unexpected response structure")
                return ""
                
        except asyncio.TimeoutError:
            print(f"  Timeout after 60 seconds")
            return ""
        except Exception as e:
            print(f"  Error generating image: {e}")
            import traceback
            traceback.print_exc()
            return ""
            
    async def _wait_for_image_task(self, session: aiohttp.ClientSession, task_id: str, session_id: str, index: int = None) -> str:
        """이미지 생성 작업 완료 대기"""
        max_attempts = 120  # 최대 6분 대기 (3초 간격)
        attempt = 0
        start_time = time.time()
        
        # 작업 상태 확인 URL - Minimax API에 맞게 수정 필요
        check_url = f"{self.base_url}/query/image_generation"
        
        print(f"  ⏱️  Waiting for image generation task: {task_id}")
        
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
                                error_msg = f"Query error: {base_resp.get('status_code')} - {base_resp.get('status_msg')}"
                                print(f"  ❌ {error_msg}")
                                raise RuntimeError(error_msg)
                        
                        # 작업 완료 확인
                        if "data" in result:
                            data = result["data"]
                            status = data.get("status", "")
                            
                            if status in ["finished", "completed", "success", "FINISHED", "COMPLETED", "SUCCESS"]:
                                elapsed_time = int(time.time() - start_time)
                                print(f"  ✅ Image generated successfully in {elapsed_time} seconds")
                                
                            if status in ["finished", "completed", "success", "FINISHED", "COMPLETED", "SUCCESS", "Success"]:
                                elapsed_time = int(time.time() - start_time)
                                print(f"  ✅ Image generated successfully in {elapsed_time} seconds")
                                
                                # image_urls 형식으로 반환되는 경우
                                if "image_urls" in data and len(data["image_urls"]) > 0:
                                    image_url = data["image_urls"][0]
                                    return await self._download_image(session, image_url, index, session_id)
                                # images 형식으로 반환되는 경우
                                elif "images" in data and len(data["images"]) > 0:
                                    image_info = data["images"][0]
                                    if "url" in image_info:
                                        return await self._download_image(session, image_info["url"], index, session_id)
                                        
                                # URL을 찾을 수 없는 경우
                                error_msg = "Image generated but no URL found in response"
                                print(f"  ❌ {error_msg}")
                                raise RuntimeError(error_msg)
                                
                            elif status in ["failed", "error", "FAILED", "ERROR"]:
                                error_msg = "Image generation failed"
                                print(f"  ❌ {error_msg}")
                                raise RuntimeError(error_msg)
                            else:
                                # 진행 상황을 덜 자주 출력 (15초마다)
                                if attempt % 5 == 0:
                                    elapsed_time = int(time.time() - start_time)
                                    print(f"  🔄 Still generating... ({elapsed_time}s elapsed)")
                        
            except RuntimeError:
                # 이미 처리된 에러는 다시 발생
                raise
            except Exception as e:
                print(f"  ⚠️  Error checking task status: {e}")
                
            await asyncio.sleep(3)  # 3초마다 확인
            attempt += 1
            
        # 타임아웃 발생
        timeout_msg = f"Image generation timeout after {(max_attempts * 3) // 60} minutes"
        print(f"  ⏰ {timeout_msg}")
        raise RuntimeError(timeout_msg)
            
    async def _download_image(self, session: aiohttp.ClientSession, url: str, index: int, session_id: str = None) -> str:
        """URL에서 이미지 다운로드"""
        try:
            print(f"  Downloading image from URL...")
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
                    
                    # 프로젝트별 구분을 위해 session_id 추가
                    image_filename = f"image_{session_id}_{index}.{ext}" if session_id else f"image_{index}.{ext}"
                    image_path = os.path.join(self.image_dir, image_filename)
                    with open(image_path, 'wb') as f:
                        f.write(content)
                    print(f"  ✓ Image saved: {os.path.basename(image_path)}")
                    
                    return image_path
                else:
                    print(f"  ✗ Failed to download image: HTTP {response.status}")
                    print(f"  Response: {await response.text()}")
        except asyncio.TimeoutError:
            print(f"  ✗ Timeout downloading image")
        except Exception as e:
            print(f"  ✗ Error downloading image: {e}")
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
    
    async def create_videos(self, images: List[str], prompts: List[str] = None, session_id: str = None) -> List[str]:
        """이미지 리스트를 받아 비디오 생성 - 체크포인트 지원, 2개씩 병렬 처리"""
        if not self.api_key:
            raise RuntimeError("MINIMAX_API_KEY not set in .env file")
            
        # 세션 ID 생성 또는 사용
        if session_id is None:
            session_id = self._create_session_id()
        
        # 체크포인트 로드
        checkpoint = self._load_checkpoint(session_id)
        
        total_start_time = time.time()
        
        print(f"\n{'='*60}")
        print(f"Starting BATCH video generation for {len(images)} images")
        print(f"Session ID: {session_id}")
        print(f"Processing 2 videos at a time (parallel batches)")
        print(f"Using model: I2V-01-live (4 seconds each)")
        print(f"⚠️  Process will STOP on first failure")
        print(f"🔄 Resume from checkpoint if available")
        print(f"{'='*60}")
        
        print(f"\n{'='*60}")
        print(f"Starting SEQUENTIAL video generation for {len(images)} images")
        print(f"Session ID: {session_id}")
        print(f"Processing 1 video at a time (safest for API limits)")
        print(f"Using model: I2V-01-live (2 seconds each)")
        print(f"⚠️  Process will STOP on first failure")
        print(f"🔄 Resume from checkpoint if available")
        print(f"{'='*60}")
        
        print(f"\n{'='*60}")
        print(f"Starting BATCH video generation for {len(images)} images")
        print(f"Session ID: {session_id}")
        print(f"Processing 2 videos at a time (optimized batch)")
        print(f"Using model: I2V-01-live (2 seconds each)")
        print(f"⚠️  Process will STOP on first failure")
        print(f"🔄 Resume from checkpoint if available")
        print(f"{'='*60}")
        
        # 체크포인트에서 이미 완료된 비디오들 확인
        completed_videos = checkpoint.get('completed_videos', [])
        video_paths = checkpoint.get('video_paths', [])
        
        # 완료된 개수 확인
        start_index = len(completed_videos)
        if start_index > 0:
            print(f"\n🔄 RESUMING FROM CHECKPOINT:")
            print(f"   Already completed: {start_index}/{len(images)} videos")
            print(f"   Starting from video {start_index + 1}")
        
        # 체크포인트 초기화 또는 비디오 단계로 업데이트
        if 'session_id' not in checkpoint:
            checkpoint = {
                'session_id': session_id,
                'total_images': len(images),
                'images': images,
                'prompts': prompts,
                'completed_videos': [],
                'video_paths': [],
                'start_time': total_start_time,
                'phase': 'video_generation'
            }
        else:
            # 이미지 생성에서 비디오 생성으로 단계 변경
            checkpoint['phase'] = 'video_generation'
            checkpoint['images'] = images
            checkpoint['prompts'] = prompts
            checkpoint['video_start_time'] = total_start_time
            
        self._save_checkpoint(session_id, checkpoint)
        
        # 남은 이미지들만 처리
        remaining_images = images[start_index:]
        if not remaining_images:
            print(f"✅ All videos already completed!")
            return video_paths
        
        # 2개씩 배치 처리 (더 효율적)
        batch_size = 2
        for batch_start in range(0, len(remaining_images), batch_size):
            batch_end = min(batch_start + batch_size, len(remaining_images))
            batch_images = remaining_images[batch_start:batch_end]
            
            actual_start = start_index + batch_start
            actual_end = start_index + batch_end
            
            print(f"\n🔄 Processing batch {batch_start//batch_size + 1}/{(len(remaining_images) + batch_size - 1)//batch_size}")
            print(f"   Videos {actual_start + 1}-{actual_end}")
            
            # 배치 실행
            batch_results = []  # 초기화 추가
            
            async def create_single_video(index: int, image_path: str):
                real_index = actual_start + index
                
                if not image_path or not os.path.exists(image_path):
                    error_msg = f"No image available for video {real_index+1}"
                    print(f"[Video {real_index+1}/{len(images)}] ❌ {error_msg}")
                    raise RuntimeError(error_msg)
                
                # 해당 장면의 프롬프트 가져오기
                scene_prompt = prompts[real_index] if prompts and real_index < len(prompts) else None
                
                print(f"[Video {real_index+1}/{len(images)}] 🚀 Starting batch generation...")
                print(f"  📁 Image: {os.path.basename(image_path)}")
                if scene_prompt:
                    print(f"  📝 Prompt: {scene_prompt[:50]}...")
                
                async with aiohttp.ClientSession() as session:
                    try:
                        video_start_time = time.time()
                        video_path = await self._create_single_video(session, image_path, real_index, scene_prompt, session_id)
                        video_time = int(time.time() - video_start_time)
                        
                        if video_path:
                            print(f"[Video {real_index+1}/{len(images)}] ✅ Completed in {video_time}s")
                            return real_index, video_path
                        else:
                            error_msg = f"Failed to create video {real_index+1} after {video_time}s"
                            print(f"[Video {real_index+1}/{len(images)}] ❌ {error_msg}")
                            raise RuntimeError(error_msg)
                            
                    except Exception as e:
                        error_msg = f"Error creating video {real_index+1}: {e}"
                        print(f"[Video {real_index+1}/{len(images)}] ❌ {error_msg}")
                        raise RuntimeError(error_msg)
            
            tasks = [create_single_video(i, image_path) for i, image_path in enumerate(batch_images)]
            batch_results = await asyncio.gather(*tasks)  # return_exceptions=True 제거
            
            try:
                # 성공한 결과들 추가 및 체크포인트 업데이트
                for real_index, video_path in batch_results:
                    video_paths.append(video_path)
                    completed_videos.append(real_index)
                    
                    # 각 비디오 완료 후 체크포인트 저장
                    checkpoint['completed_videos'] = completed_videos
                    checkpoint['video_paths'] = video_paths
                    checkpoint['last_completed_index'] = real_index
                    checkpoint['last_update'] = time.time()
                    self._save_checkpoint(session_id, checkpoint)
                    
            except Exception as e:
                # 실패 시 체크포인트 저장 후 중단
                failed_index = actual_start + len(batch_results)  # 이제 batch_results가 항상 정의됨
                checkpoint['failed_at'] = {
                    'index': failed_index,
                    'error': str(e),
                    'timestamp': time.time()
                }
                self._save_checkpoint(session_id, checkpoint)
                
                print(f"\n{'='*60}")
                print(f"❌ VIDEO GENERATION FAILED - STOPPING PROCESS")
                print(f"Error: {e}")
                print(f"Completed videos: {len(completed_videos)}/{len(images)}")
                print(f"💾 Progress saved to checkpoint: {session_id}")
                print(f"🔄 To resume, use the same session_id: {session_id}")
                print(f"{'='*60}")
                raise RuntimeError(f"Video generation failed: {e}")
            
            # 배치 간 대기 (API 제한 방지)
            if actual_end < len(images):
                print(f"⏳ Waiting 5 seconds before next batch...")
                await asyncio.sleep(5)
        
            # 배치 간 대기 (API 제한 방지)
            if actual_end < len(images):
                print(f"⏳ Waiting 10 seconds before next batch...")
                await asyncio.sleep(10)
        
        total_time = int(time.time() - total_start_time)
        success_count = len(video_paths)
        
        # 완료 체크포인트 업데이트
        checkpoint['completed'] = True
        checkpoint['completion_time'] = time.time()
        checkpoint['video_total_time'] = total_time
        self._save_checkpoint(session_id, checkpoint)
        
        print(f"\n{'='*60}")
        print(f"🎉 ALL VIDEOS GENERATED SUCCESSFULLY!")
        print(f"  Session ID: {session_id}")
        print(f"  Total time: {total_time // 60}m {total_time % 60}s")
        print(f"  Success rate: {success_count}/{len(images)}")
        print(f"  Average time per video: {total_time // len(images) if images else 0}s")
        print(f"  Time saved with parallel processing: ~{len(images) * 3 - total_time // 60}+ minutes!")
        print(f"{'='*60}\n")
        
        # 모든 작업 완료 시 체크포인트 삭제 (선택사항)
        # self._clear_checkpoint(session_id)
                
        return video_paths
        
    async def _create_single_video(self, session: aiohttp.ClientSession, image_path: str, index: int, scene_prompt: str = None, session_id: str = None) -> str:
        """단일 이미지로 비디오 생성"""
        try:
            # 이미지를 base64로 인코딩
            with open(image_path, "rb") as img_file:
                image_base64 = base64.b64encode(img_file.read()).decode()
            
            # Minimax Video Generation API 호출
            url = f"{self.base_url}/video_generation"
            
            # 동적 프롬프트 생성
            if scene_prompt:
                # 비디오 생성에 최적화된 프롬프트
                video_prompt = scene_prompt
            else:
                # 기본 프롬프트
                video_prompt = "Create smooth, natural camera movement and bring the scene to life with subtle animations"
            
            # I2V 모델 선택 - 더 빠른 모델 사용
            # I2V-01: 표준 모델, 균형잡힌 품질과 속도
            # I2V-01-live: 더 빠른 처리, 라이브 스트리밍에 최적화
            model_choice = "I2V-01-live"  # 더 빠른 처리를 위해 live 버전 사용
            
            payload = {
                "model": model_choice,
                "prompt": video_prompt[:200],  # 프롬프트 길이 더욱 단축 (500 -> 200)
                "first_frame_image": f"data:image/jpeg;base64,{image_base64}",
                "parameters": {
                    "prompt_optimizer": False,  # 빠른 처리를 위해 비활성화
                    "motion_strength": 0.1,  # 움직임 강도 더욱 최소화 (0.3 -> 0.1)
                    "video_length": 2  # 비디오 길이 최소화 (4초 -> 2초)
                }
            }
            
            print(f"  🎬 Creating {payload['parameters']['video_length']}s video...")
            print(f"  📝 Prompt: {video_prompt[:60]}...")
            print(f"  🖼️  Image: {os.path.basename(image_path)}")
            print(f"  Starting video generation...")
            
            async with session.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=600)  # 5분 타임아웃
            ) as response:
                response_text = await response.text()
                print(f"  API Response status: {response.status}")
                
                if response.status != 200:
                    print(f"  API Error: {response.status}")
                    print(f"  Error details: {response_text[:500]}")
                    return ""
                    
                result = json.loads(response_text)
                
                # base_resp 체크
                if "base_resp" in result:
                    base_resp = result["base_resp"]
                    if base_resp.get("status_code") != 0:
                        print(f"  API error: {base_resp.get('status_code')} - {base_resp.get('status_msg')}")
                        return ""
                
                # 성공적인 응답 처리 - task_id 반환
                task_id = None
                if "task_id" in result:
                    task_id = result["task_id"]
                elif "data" in result and "task_id" in result["data"]:
                    task_id = result["data"]["task_id"]
                    
                if task_id:
                    print(f"  Task created successfully: {task_id}")
                    print(f"  Waiting for video generation to complete...")
                    
                    file_id = await self._wait_for_video_task(session, task_id)
                    if file_id:
                        # file_id가 실제로 URL인 경우 (직접 URL 반환)
                        if file_id.startswith("http"):
                            print(f"  Direct video URL received")
                            return await self._download_video(session, file_id, index, session_id)
                        else:
                            # file_id인 경우 retrieve API 호출
                            print(f"  Retrieving download URL for file_id: {file_id}")
                            video_url = await self._get_file_url(session, file_id)
                            if video_url:
                                return await self._download_video(session, video_url, index, session_id)
                            else:
                                print(f"  Failed to retrieve download URL")
                                return ""
                    else:
                        print(f"  Video generation failed or timed out")
                        return ""
                else:
                    print(f"  No task_id in response")
                    print(f"  Response structure: {json.dumps(result, indent=2)[:500]}")
                return ""
                
        except asyncio.TimeoutError:
            print(f"  Timeout creating video after 5 minutes")
            return ""
        except Exception as e:
            print(f"  Error in video creation: {e}")
            import traceback
            traceback.print_exc()
            return ""
            
    async def _wait_for_video_task(self, session: aiohttp.ClientSession, task_id: str) -> str:
        """비디오 생성 작업 완료 대기 - file_id 반환"""
        max_attempts = 1200  # 최대 10분 대기 (2초 간격, 테스트용 더 단축)
        attempt = 0
        last_status = None
        start_time = time.time()
        
        # 비디오 작업 상태 확인 URL
        check_url = f"{self.base_url}/query/video_generation"
        
        print(f"  ⏱️  Monitoring task: {task_id}")
        print(f"  Expected: 1-5 minutes (I2V-01-live model, 2s videos, 5min timeout)")
        
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
                        
                        # 상세 로그는 처음 몇 번과 상태 변경 시에만 출력
                        if attempt < 3 or (attempt % 15 == 0):  # 30초마다
                            print(f"  📊 Check #{attempt+1}: {json.dumps(result, indent=2)[:200]}...")
                        
                        # base_resp 체크
                        if "base_resp" in result:
                            base_resp = result["base_resp"]
                            if base_resp.get("status_code") != 0:
                                error_msg = f"Query error: {base_resp.get('status_code')} - {base_resp.get('status_msg')}"
                                print(f"  ❌ {error_msg}")
                                raise RuntimeError(error_msg)
                        
                        # 다양한 상태 필드 확인
                        status = None
                        
                        # status 확인 (여러 위치에서)
                        if "status" in result:
                            status = result["status"]
                        elif "data" in result and "status" in result["data"]:
                            status = result["data"]["status"]
                        elif "task_status" in result:
                            status = result["task_status"]
                            
                        # 상태가 변경되었거나 30초마다 업데이트
                        if status != last_status or (attempt % 15 == 0):
                            elapsed_time = int(time.time() - start_time)
                            elapsed_min = elapsed_time // 60
                            elapsed_sec = elapsed_time % 60
                            print(f"  🔄 [{elapsed_min}:{elapsed_sec:02d}] Status: {status}")
                            last_status = status
                        
                        # 완료 상태 확인
                        if status in ["finished", "success", "completed", "done", "FINISHED", "SUCCESS", "COMPLETED", "Success"]:
                            elapsed_time = int(time.time() - start_time)
                            print(f"  ✅ Completed in {elapsed_time}s!")
                            
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
                        
                            # file_id나 URL을 찾을 수 없는 경우
                            error_msg = "Video generated but no file_id or URL found in response"
                            print(f"  ❌ {error_msg}")
                            raise RuntimeError(error_msg)
                        
                        elif status in ["failed", "error", "FAILED", "ERROR", "Fail"]:
                            elapsed_time = int(time.time() - start_time)
                            error_msg = result.get("message") or result.get("error_msg") or "Unknown error"
                            full_error = f"Video generation failed after {elapsed_time}s: {error_msg}"
                            print(f"  ❌ {full_error}")
                            raise RuntimeError(full_error)
                        
                        # 진행 중인 경우 계속 대기
                        elif status in ["processing", "pending", "queued", "running", "PROCESSING", "PENDING", "QUEUED", "RUNNING"]:
                            # 진행률이 있으면 표시
                            progress = None
                            if "progress" in result:
                                progress = result["progress"]
                            elif "data" in result and "progress" in result["data"]:
                                progress = result["data"]["progress"]
                                
                            if progress is not None and progress > 0:
                                print(f"  📈 Progress: {progress}%")
                        
                        # 진행 중인 경우 계속 대기
                        elif status in ["processing", "pending", "queued", "running", "PROCESSING", "PENDING", "QUEUED", "RUNNING", "Processing", "Preparing", "Queueing"]:
                            # 진행률이 있으면 표시
                            progress = None
                            if "progress" in result:
                                progress = result["progress"]
                            elif "data" in result and "progress" in result["data"]:
                                progress = result["data"]["progress"]
                                
                            if progress is not None and progress > 0:
                                print(f"  📈 Progress: {progress}%")
                    else:
                        print(f"  ⚠️  Status check failed: HTTP {response.status}")
                        
            except RuntimeError:
                # 이미 처리된 에러는 다시 발생
                raise
            except Exception as e:
                if attempt % 30 == 0:  # 1분마다만 에러 로그 출력
                    print(f"  ⚠️  Network error (attempt {attempt}): {e}")
                
            # 2초마다 확인 (기존 3초에서 단축)
            await asyncio.sleep(2)
            attempt += 1
            
        # 타임아웃 발생
        total_time = int(time.time() - start_time)
        timeout_msg = f"Video generation timeout after {total_time // 60}m {total_time % 60}s"
        print(f"  ⏰ {timeout_msg}")
        raise RuntimeError(timeout_msg)
        
    async def _get_file_url(self, session: aiohttp.ClientSession, file_id: str) -> str:
        """file_id로 다운로드 URL 획득"""
        try:
            # Files Retrieve API 사용 - GET 요청 (예시 코드와 동일)
            url = f"{self.base_url}/files/retrieve"
            
            print(f"Retrieving file URL for file_id: {file_id}")
            print(f"API endpoint: {url}?file_id={file_id}")
            
            async with session.get(
                url,
                params={"file_id": file_id},
                headers=self.headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                response_text = await response.text()
                print(f"File retrieve response status: {response.status}")
                print(f"Response: {response_text[:500]}...")
                
                if response.status == 200:
                    result = json.loads(response_text)
                    
                    # base_resp 체크
                    if "base_resp" in result:
                        base_resp = result["base_resp"]
                        if base_resp.get("status_code") != 0:
                            print(f"File retrieve error: {base_resp.get('status_code')} - {base_resp.get('status_msg')}")
                            return ""
                    
                    # 다양한 위치에서 URL 찾기
                    if "file" in result and "download_url" in result["file"]:
                        return result["file"]["download_url"]
                    elif "download_url" in result:
                        return result["download_url"]
                    elif "url" in result:
                        return result["url"]
                    elif "data" in result:
                        data = result["data"]
                        if "download_url" in data:
                            return data["download_url"]
                        elif "url" in data:
                            return data["url"]
                        elif "file" in data and "download_url" in data["file"]:
                            return data["file"]["download_url"]
                            
                    print(f"Could not find download URL in response: {json.dumps(result, indent=2)}")
                else:
                    print(f"Failed to get file URL: HTTP {response.status}")
                    print(f"Error response: {await response.text()}")
                    
        except Exception as e:
            print(f"Error getting file URL: {e}")
            import traceback
            traceback.print_exc()
            
        return ""
        
    async def _download_video(self, session: aiohttp.ClientSession, url: str, index: int, session_id: str = None) -> str:
        """URL에서 비디오 다운로드"""
        try:
            print(f"  Downloading video file...")
            
            # 비디오 파일은 크기가 클 수 있으므로 충분한 타임아웃 설정
            async with session.get(
                url, 
                timeout=aiohttp.ClientTimeout(total=1200)  # 5분 타임아웃
            ) as response:
                if response.status == 200:
                    # 파일 크기 확인
                    content_length = response.headers.get('Content-Length')
                    if content_length:
                        print(f"  Video file size: {int(content_length) / (1024*1024):.2f} MB")
                    
                    content = await response.read()
                    video_path = os.path.join(self.video_dir, f"video_{index}.mp4")
                    
                    # 프로젝트별 구분을 위해 session_id 추가
                    video_filename = f"video_{session_id}_{index}.mp4" if session_id else f"video_{index}.mp4"
                    video_path = os.path.join(self.video_dir, video_filename)
                    
                    with open(video_path, 'wb') as f:
                        f.write(content)
                    
                    # 파일이 제대로 저장되었는지 확인
                    if os.path.exists(video_path):
                        file_size = os.path.getsize(video_path)
                        print(f"  ✓ Video saved: {os.path.basename(video_path)} ({file_size / (1024*1024):.2f} MB)")
                    return video_path
                    else:
                        print(f"  ✗ Failed to save video file")
                        return ""
                else:
                    print(f"  ✗ Failed to download video: HTTP {response.status}")
                    error_text = await response.text()
                    print(f"  Error response: {error_text[:300]}")
                    return ""
                    
        except asyncio.TimeoutError:
            print(f"  ✗ Timeout downloading video after 5 minutes")
        except Exception as e:
            print(f"  ✗ Error downloading video: {e}")
            
        return ""