# app/services/openai_service.py
from openai import AsyncOpenAI
from typing import List, Dict, Tuple
import asyncio
import os
import base64
import json

class OpenAIService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = AsyncOpenAI(api_key=api_key)
        else:
            self.client = None
            
    async def select_best_image_and_create_video_prompt(self, image_paths: List[str], original_prompts: List[str], user_description: str, uploaded_image_path: str) -> Tuple[int, str, str]:
        """
        생성된 이미지들 중 가장 적합한 이미지를 선택하고, 해당 이미지에 최적화된 비디오 프롬프트를 생성
        
        Args:
            image_paths: 생성된 이미지 파일 경로들
            original_prompts: 원본 이미지 생성 프롬프트들
            user_description: 사용자가 입력한 설명
            uploaded_image_path: 사용자가 업로드한 원본 강아지 사진
            
        Returns:
            (선택된_이미지_인덱스, 선택_이유, 비디오_프롬프트)
        """
        
        if len(image_paths) <= 1:
            return 0, "Only one image available", "Smooth cinematic movement bringing the scene to life"
        
        try:
            # 업로드된 원본 이미지 인코딩
            with open(uploaded_image_path, "rb") as image_file:
                original_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 생성된 이미지들 인코딩
            image_data_list = []
            for i, image_path in enumerate(image_paths):
                try:
                    with open(image_path, "rb") as image_file:
                        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                        image_data_list.append({
                            "index": i,
                            "data": base64_image,
                            "prompt": original_prompts[i] if i < len(original_prompts) else "No prompt available"
                        })
                except Exception as e:
                    print(f"Error loading image {i}: {e}")
                    continue
            
            if not image_data_list:
                return 0, "No valid images found", "Smooth cinematic movement bringing the scene to life"
            
            # OpenAI Vision으로 이미지 분석 및 선택
            messages = [
                {
                    "role": "system",
                    "content": """You are an expert at selecting the best image for video generation and creating optimized video prompts.

Analyze the provided images and:
1. Select the image that best matches the user's description and original pet photo
2. Create an optimized video prompt for the selected image

Consider these criteria for image selection:
- Visual quality and clarity
- Similarity to the original pet photo (breed, color, characteristics)
- Relevance to user's description
- Suitability for video animation
- Composition and lighting

For video prompt creation:
- 15-25 words describing natural movements
- Natural, realistic motion
- Cinematic quality
- Works well with the selected image as starting frame

Return ONLY a JSON object in this format:
{
    "selected_index": 0,
    "reason": "Brief explanation of why this image is best",
    "video_prompt": "Optimized video prompt for smooth natural animation"
}"""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"User Description: {user_description}\n\nOriginal Pet Photo:"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{original_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": f"Select the best image from these {len(image_data_list)} generated options and create a natural video prompt:"
                        }
                    ] + [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_data['data']}"
                            }
                        } for img_data in image_data_list
                    ]
                }
            ]
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.3,
                max_tokens=300
            )
            
            response_text = response.choices[0].message.content.strip()
            print(f"OpenAI selection response: {response_text}")
            
            # JSON 마크다운 제거 및 파싱
            try:
                # ```json 및 ``` 제거
                clean_text = response_text
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                
                result = json.loads(clean_text)
                selected_index = result.get("selected_index", 0)
                reason = result.get("reason", "AI selected this image as most suitable")
                video_prompt = result.get("video_prompt", "Smooth cinematic movement bringing the scene to life")
                
                # 인덱스 유효성 검사
                if 0 <= selected_index < len(image_paths):
                    return selected_index, reason, video_prompt
                else:
                    return 0, f"Invalid index {selected_index}, using first image", video_prompt
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                return 0, "Failed to parse selection response, using first image", "Smooth cinematic movement bringing the scene to life"
                
        except Exception as e:
            print(f"Error in image selection and video prompt creation: {e}")
            return 0, f"Error during selection: {str(e)}, using first image", "Smooth cinematic movement bringing the scene to life"

    async def generate_step_prompts_from_image_and_description(self, image_path: str, description: str, num_steps: int = 5) -> List[str]:
        """
        1단계: OpenAI Vision API로 강아지 이미지와 설명을 분석해서 Minimax용 단계별 이미지 생성 프롬프트들을 생성
        
        Args:
            image_path: 업로드된 강아지 사진 경로
            description: 사용자 설명
            num_steps: 생성할 단계 수
            
        Returns:
            List of step prompts for Minimax image generation
        """
        
        try:
            # 이미지를 base64로 인코딩
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # OpenAI Vision API로 단계별 프롬프트 생성 요청
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""이 반려동물 사진을 보고, 사용자 스토리에 맞는 5단계 장면을 간단한 영어로 만들어주세요.

사용자 스토리: {description}

각 단계별로 3-6단어의 매우 간단한 영어 동작 설명을 만들어주세요:
- 예시: "pet in box", "pet being held", "pet at home", "pet playing", "pet sleeping"
- 반려동물의 품종이나 외모는 언급하지 마세요
- 오직 장면과 동작만 설명하세요
- 자연스럽고 안전한 일상 장면으로 만들어주세요

JSON 배열 형태로 답변해주세요:
["step1 action", "step2 action", "step3 action", "step4 action", "step5 action"]"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content.strip()
            print(f"OpenAI step prompts response: {response_text[:200]}...")
            
            # JSON 마크다운 제거 및 파싱
            try:
                # ```json 및 ``` 제거
                clean_text = response_text
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                
                prompts = json.loads(clean_text)
                
                if isinstance(prompts, list) and len(prompts) == num_steps:
                    print(f"✅ Generated {len(prompts)} step prompts successfully")
                    return prompts
                else:
                    print(f"Invalid response format, expected {num_steps} prompts, got {len(prompts) if isinstance(prompts, list) else 'non-list'}")
                    return self._generate_fallback_step_prompts(description, num_steps)
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                return self._generate_fallback_step_prompts(description, num_steps)
                
        except Exception as e:
            print(f"Error generating step prompts with OpenAI: {e}")
            return self._generate_fallback_step_prompts(description, num_steps)
    
    def _generate_fallback_step_prompts(self, description: str, num_steps: int) -> List[str]:
        """Fallback 단계별 프롬프트 생성"""
        # 사용자 설명을 기반으로 5단계 스토리 생성
        if "박스" in description and "강아지" in description:
            # 겨울 박스 구조 스토리
            return [
                "pet in box on snowy street",
                "pet being discovered in box",
                "pet being gently held",
                "pet at warm home",
                "pet playing happily indoors"
            ]
        elif "뛰어" in description or "달려" in description:
            # 뛰어오는 스토리
            return [
                "pet sitting calmly",
                "pet noticing something",
                "pet starting to run",
                "pet running joyfully",
                "pet reaching destination"
            ]
        else:
            # 기본 일상 스토리
            return [
                "pet resting peacefully",
                "pet looking around curiously", 
                "pet standing up",
                "pet moving around",
                "pet playing happily"
            ] 

    async def generate_video_prompt_from_user_image(self, image_path: str, user_description: str) -> str:
        """
        사용자 업로드 이미지로부터 직접 영상 프롬프트 생성
        
        Args:
            image_path: 사용자가 업로드한 이미지 경로
            user_description: 사용자가 원하는 영상 설명
            
        Returns:
            Generated video prompt for Minimax video generation
        """
        
        try:
            # 이미지를 base64로 인코딩
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # OpenAI Vision API로 영상 프롬프트 생성 요청
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""이 이미지를 첫 프레임으로 사용하여 영상을 만들고 싶습니다.

사용자 요청: {user_description}

이 이미지의 내용을 분석하고, 사용자 요청에 맞는 자연스러운 영상 프롬프트를 만들어주세요.

요구사항:
- 이미지의 인물/객체/배경을 기반으로 구성
- 사용자 요청에 맞는 자연스러운 움직임과 행동
- 15-25단어의 영어 프롬프트로 작성
- 현실적이고 부드러운 움직임 설명
- 카메라 워크와 분위기 포함

영상 프롬프트 작성 가이드:
- 움직임: "walking slowly", "looking around", "gentle movement" 등
- 카메라: "camera follows", "slow zoom", "steady shot" 등  
- 분위기: "cinematic lighting", "natural movement", "peaceful scene" 등

단일 영상 프롬프트로 답변해주세요 (JSON 배열이 아닌 문자열로):"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            video_prompt = response.choices[0].message.content.strip()
            print(f"✅ Generated video prompt from user image: {video_prompt[:50]}...")
            
            return video_prompt
            
        except Exception as e:
            print(f"Error generating video prompt from user image: {e}")
            # Fallback 프롬프트
            return f"Natural cinematic movement based on the scene, {user_description}, smooth camera work, realistic motion" 

    async def generate_story_prompts_from_images(self, image_paths: List[str], user_description: str) -> List[str]:
        """
        여러 이미지들로부터 순서대로 스토리 기반 영상 프롬프트 생성
        
        Args:
            image_paths: 업로드된 이미지들의 경로 리스트
            user_description: 사용자가 원하는 스토리 설명
            
        Returns:
            List of Midjourney-style story prompts for each image
        """
        
        try:
            num_images = len(image_paths)
            if num_images == 0:
                return []
            
            # 모든 이미지를 base64로 인코딩
            image_data = []
            for i, image_path in enumerate(image_paths):
                with open(image_path, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                    image_data.append({
                        "index": i + 1,
                        "data": base64_image
                    })
            
            # OpenAI Vision API로 스토리 기반 프롬프트 생성 요청
            content = [
                {
                    "type": "text",
                    "text": f"""이 {num_images}개의 이미지들을 보고, 사용자 스토리에 맞는 순서대로 연결된 {num_images}단계 스토리를 만들어주세요.

사용자 스토리: {user_description}

요구사항:
- {num_images}개 이미지 순서대로 자연스럽게 연결되는 스토리 구성
- 각 단계는 Midjourney 스타일의 상세한 영어 프롬프트로 작성
- 각 프롬프트는 25-35단어로 구성
- 미드저니 문법 포함: --ar 3:2 --style [스타일] --v 6
- 스타일 옵션: cinematic, photorealistic, cozy lighting, warm tone, domestic, playful, joyful, energetic 등
- 각 단계가 하나의 완전한 스토리를 만들도록 구성

예시 형식:
"A lonely cardboard box sits on a snowy street under a lamppost on a freezing winter night. --ar 3:2 --style cinematic --v 6"

JSON 배열 형태로 답변해주세요:
["step1 midjourney prompt", "step2 midjourney prompt", ..., "step{num_images} midjourney prompt"]"""
                }
            ]
            
            # 각 이미지를 content에 추가
            for img_data in image_data:
                content.append({
                    "type": "text", 
                    "text": f"Image {img_data['index']}:"
                })
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_data['data']}"
                    }
                })
            
            messages = [
                {
                    "role": "user",
                    "content": content
                }
            ]
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content.strip()
            print(f"✅ Generated {num_images} story prompts: {response_text[:200]}...")
            
            # JSON 마크다운 제거 및 파싱
            try:
                # ```json 및 ``` 제거
                clean_text = response_text
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                
                prompts = json.loads(clean_text)
                
                if isinstance(prompts, list) and len(prompts) == num_images:
                    print(f"✅ Generated {len(prompts)} story prompts successfully")
                    return prompts
                else:
                    print(f"Invalid response format, expected {num_images} prompts, got {len(prompts) if isinstance(prompts, list) else 'non-list'}")
                    return self._generate_fallback_story_prompts(user_description, num_images)
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                return self._generate_fallback_story_prompts(user_description, num_images)
                
        except Exception as e:
            print(f"Error generating story prompts: {e}")
            return self._generate_fallback_story_prompts(user_description, num_images)
    
    def _generate_fallback_story_prompts(self, user_description: str, num_images: int) -> List[str]:
        """Fallback 스토리 프롬프트 생성"""
        
        # 기본 스토리 템플릿
        if "구조" in user_description or "rescue" in user_description.lower():
            # 구조 스토리
            base_story = [
                "A lonely cardboard box sits on a snowy street under a lamppost on a freezing winter night. --ar 3:2 --style cinematic --v 6",
                "A person in warm winter clothes notices the box and approaches it slowly in the snow. --ar 3:2 --style cinematic --v 6", 
                "The person carefully opens the box, revealing a frightened, shivering puppy inside. --ar 3:2 --style photorealistic --v 6",
                "The person gently holds the cold puppy close, wrapping it warmly and walking away from the snow. --ar 3:2 --style cinematic --v 6",
                "At home, the person hugs the puppy warmly under soft indoor lighting. --ar 3:2 --style cozy lighting --v 6",
                "The puppy sits curled up in a corner of the room, looking nervous and unsure in the new place. --ar 3:2 --style warm tone --v 6",
                "The puppy slowly begins to eat from a bowl, its body relaxed and more comfortable. --ar 3:2 --style domestic --v 6",
                "The puppy happily plays with several toys scattered across a cozy living room carpet. --ar 3:2 --style playful --v 6",
                "The puppy looks up at the person with a big smile, eyes full of trust and happiness. --ar 3:2 --style joyful --v 6",
                "The puppy runs toward the camera, full of energy and joy, as if greeting its best friend. --ar 3:2 --style energetic --v 6"
            ]
        else:
            # 일반적인 강아지 일상 스토리
            base_story = [
                "A cute dog sits peacefully in a beautiful outdoor setting with natural lighting. --ar 3:2 --style cinematic --v 6",
                "The same dog begins to move around, exploring its surroundings with curiosity. --ar 3:2 --style photorealistic --v 6",
                "The dog discovers something interesting and approaches it with excitement. --ar 3:2 --style cinematic --v 6", 
                "The dog plays happily, showing joy and energy in a warm, inviting environment. --ar 3:2 --style playful --v 6",
                "The dog interacts with its environment, displaying natural and endearing behavior. --ar 3:2 --style cozy lighting --v 6",
                "The dog enjoys a peaceful moment, resting in a comfortable and safe place. --ar 3:2 --style warm tone --v 6",
                "The dog shows affection and trust, creating a heartwarming scene. --ar 3:2 --style joyful --v 6",
                "The dog engages in playful activity, demonstrating its personality and charm. --ar 3:2 --style domestic --v 6",
                "The dog looks directly at the camera with a friendly and welcoming expression. --ar 3:2 --style energetic --v 6",
                "The dog runs with pure joy and freedom, embodying happiness and vitality. --ar 3:2 --style cinematic --v 6"
            ]
        
        # 요청된 이미지 수만큼 반환
        return base_story[:num_images] 

    async def generate_10_step_scene_descriptions(self, main_description: str, image_path: str = None) -> List[str]:
        """
        사용자의 메인 설명과 업로드된 강아지 사진을 기반으로 10단계 스토리 장면을 미드저니 형식으로 생성
        
        Args:
            main_description: 사용자가 입력한 메인 내용 설명
            image_path: 업로드된 강아지 사진 경로 (실제 강아지 특징 분석용)
            
        Returns:
            List of 10 Midjourney-style scene prompts in English based on the actual dog
        """
        
        try:
            messages = [
                {
                    "role": "system", 
                    "content": """You are a creative writing assistant that creates scene descriptions for image generation.

Create 10 scene descriptions in English based on the user's story and uploaded image.

Requirements:
1. Analyze the uploaded image to understand the subject's characteristics
2. Create 10 sequential scenes that tell a natural story
3. Each scene should be 20-30 words in English
4. Focus on actions, emotions, and environments
5. Make scenes suitable for image generation
6. Include these style parameters at the end of each prompt: --style raw --style photographic --v 6 --ar 9:16 consistent lighting

Return as JSON array:
["scene 1 description", "scene 2 description", ..., "scene 10 description"]"""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Please create 10 scene descriptions based on this image and story:

Story: {main_description}

Create 10 sequential scenes in English (20-30 words each) that tell a natural story based on the image and story above. Include --style raw --style photographic --v 6 --ar 9:16 consistent lighting at the end of each scene.

Return as JSON array format."""
                        }
                    ]
                }
            ]
            
            # 이미지가 제공된 경우 분석에 포함
            if image_path and os.path.exists(image_path):
                try:
                    with open(image_path, "rb") as image_file:
                        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                    
                    # 이미지를 메시지에 추가
                    messages[1]["content"].append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    })
                    print(f"✅ 강아지 사진 분석을 위해 이미지 포함: {image_path}")
                    
                except Exception as e:
                    print(f"⚠️ 이미지 로딩 실패: {e}")
            else:
                print(f"⚠️ 이미지 경로가 제공되지 않았거나 파일이 존재하지 않음: {image_path}")
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            
            response_text = response.choices[0].message.content.strip()
            print(f"OpenAI Midjourney prompts response: {response_text}")
            
            # OpenAI 거부 응답 체크
            if "sorry" in response_text.lower() or "can't assist" in response_text.lower() or "cannot" in response_text.lower():
                print(f"⚠️ OpenAI refused the request, using fallback prompts")
                return self._generate_fallback_midjourney_scenes(main_description)
            
            # JSON 파싱
            try:
                # JSON 마크다운 제거
                clean_text = response_text
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()
                
                scenes = json.loads(clean_text)
                
                # 배열인지 확인하고 10개인지 체크
                if isinstance(scenes, list) and len(scenes) == 10:
                    print(f"✅ Generated 10 Midjourney-style prompts based on actual dog photo")
                    for i, scene in enumerate(scenes, 1):
                        print(f"Scene {i}: {scene[:80]}...")
                    return scenes
                else:
                    print(f"Warning: Expected 10 scenes, got {len(scenes) if isinstance(scenes, list) else 'non-list'}")
                    return self._generate_fallback_midjourney_scenes(main_description)
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                return self._generate_fallback_midjourney_scenes(main_description)
                
        except Exception as e:
            print(f"Error generating 10-step Midjourney scenes: {e}")
            return self._generate_fallback_midjourney_scenes(main_description)
    
    def _generate_fallback_midjourney_scenes(self, main_description: str) -> List[str]:
        """10단계 미드저니 장면 생성 실패 시 폴백 장면들"""
        base_style = "--style raw --style photographic --v 6 --ar 9:16 consistent lighting"
        
        if "강아지" in main_description and ("유치원" in main_description or "놀이" in main_description):
            return [
                f"A photorealistic cute puppy getting ready at home, looking excited with bright eyes and wagging tail, natural lighting, professional photography. {base_style}",
                f"The same photorealistic puppy walking towards a colorful kindergarten building with other puppies visible in the background, lifelike detail. {base_style}",
                f"The realistic puppy arriving at the kindergarten entrance, meeting friendly staff and other puppies for the first time, natural scene. {base_style}",
                f"The photorealistic puppy cautiously exploring the kindergarten playground, sniffing around with curiosity and wonder, real dog behavior. {base_style}",
                f"The realistic puppy starting to play with colorful toys scattered around the kindergarten play area, natural lighting. {base_style}",
                f"The photorealistic puppy meeting and greeting other puppies, beginning to form new friendships through gentle interactions, lifelike. {base_style}",
                f"The realistic puppy actively playing with other puppies, running around together in the safe kindergarten environment, natural motion. {base_style}",
                f"The photorealistic puppy engaged in group play activities, showing joy and excitement while interacting with multiple puppies, real photo. {base_style}",
                f"The realistic puppy and friends playing their favorite games together, showing pure happiness and playful energy, professional photography. {base_style}",
                f"The tired but happy photorealistic puppy resting after playtime, surrounded by new friends in a peaceful moment, natural lighting. {base_style}"
            ]
        else:
            return [
                f"A photorealistic character preparing for an important journey or activity, showing determination and readiness, natural lighting. {base_style}",
                f"The same realistic character taking the first steps toward their goal, moving with purpose and confidence, lifelike detail. {base_style}",
                f"The photorealistic character arriving at their destination, taking in the new environment with curiosity, real photo style. {base_style}",
                f"The realistic character beginning their main activity, showing focus and initial engagement, professional photography. {base_style}",
                f"The photorealistic character becoming more involved in the activity, showing growing enthusiasm and skill, natural scene. {base_style}",
                f"The realistic character interacting with others or elements in the environment, building connections, lifelike interaction. {base_style}",
                f"The photorealistic character reaching a peak moment of activity, showing intense focus and energy, natural lighting. {base_style}",
                f"The realistic character experiencing a breakthrough or special moment, radiating joy and accomplishment, real photo. {base_style}",
                f"The photorealistic character completing their main activity with satisfaction and sense of achievement, professional photography. {base_style}",
                f"The realistic character reflecting on the experience, showing contentment and peaceful completion, natural lighting. {base_style}"
            ] 