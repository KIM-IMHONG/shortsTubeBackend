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
            
    async def analyze_dog_image(self, image_path: str) -> Dict:
        """강아지 이미지 분석"""
        try:
            # 이미지를 base64로 인코딩
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            messages = [
                {
                    "role": "system",
                    "content": """You are an expert dog breed identifier and analyst.
Analyze the provided dog image and return detailed information about the dog.

Respond with ONLY a JSON object in this format:
{
    "breed": "Dog breed name",
    "characteristics": ["characteristic1", "characteristic2", "characteristic3"],
    "size": "small/medium/large",
    "color": "primary color description",
    "age_estimate": "puppy/young/adult/senior",
    "temperament": "calm/energetic/playful/etc",
    "confidence": 0.85
}"""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please analyze this dog image and provide detailed information:"
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
                temperature=0.3,
                max_tokens=300
            )
            
            response_text = response.choices[0].message.content.strip()
            print(f"Dog analysis response: {response_text}")
            
            # JSON 마크다운 제거 및 파싱
            try:
                # ```json 및 ``` 제거
                clean_text = response_text
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]  # ```json 제거
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]   # ``` 제거
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]  # 끝의 ``` 제거
                clean_text = clean_text.strip()
                
                dog_analysis = json.loads(clean_text)
                return dog_analysis
            except json.JSONDecodeError:
                # Fallback 분석 결과
                return {
                    "breed": "Mixed Breed",
                    "characteristics": ["friendly", "intelligent", "loyal"],
                    "size": "medium",
                    "color": "brown",
                    "age_estimate": "adult",
                    "temperament": "playful",
                    "confidence": 0.5
                }
                
        except Exception as e:
            print(f"Error analyzing dog image: {e}")
            # Fallback 분석 결과
            return {
                "breed": "Mixed Breed",
                "characteristics": ["friendly", "intelligent", "loyal"],
                "size": "medium",
                "color": "brown",
                "age_estimate": "adult",
                "temperament": "playful",
                "confidence": 0.5
            }
            
    async def analyze_dog_and_generate_video_sequence(self, dog_image_path: str, description: str, content_type: str = "life") -> Tuple[Dict, List[str], List[str]]:
        """강아지 이미지와 함께 프롬프트를 OpenAI에 보내서 직접 3단계 이미지/비디오 프롬프트 생성"""
        
        try:
            # 이미지를 base64로 인코딩
            with open(dog_image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # 강아지 사진과 함께 프롬프트 생성
            messages = [
                {
                    "role": "system",
                    "content": f"""You are an expert at creating detailed video sequences for YouTube Shorts based on dog images.

Analyze the provided dog image and create exactly 3 sequential image prompts and 3 video prompts based on the user's description.

Content Type: {content_type}
- If "life" (일상생활): Focus on daily life activities like shopping, walking, playing
- If "cooking" (요리): Focus on cooking and food preparation
- If "travel" (여행): Focus on travel and exploration

Requirements:
1. Look at the actual dog in the image - use its EXACT breed, color, size, and characteristics
2. Create 3 detailed image prompts that show different scenes/moments (static scenes for image generation, 15-25 words each)
3. Create 3 corresponding video prompts that animate those images (movement and animation, 15-25 words each)
4. Each pair should work together as a cohesive story sequence
5. ALWAYS start each prompt with the EXACT dog you see in the image
6. Use the actual dog's appearance from the photo

First analyze the dog, then return ONLY a JSON object in this format:
{{
    "dog_analysis": {{
        "breed": "actual breed from image",
        "characteristics": ["characteristic1", "characteristic2", "characteristic3"],
        "size": "small/medium/large",
        "color": "actual color from image",
        "age_estimate": "puppy/young/adult/senior",
        "temperament": "observed temperament",
        "confidence": 0.95
    }},
    "image_prompts": ["prompt1", "prompt2", "prompt3"],
    "video_prompts": ["prompt1", "prompt2", "prompt3"]
}}"""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Please look at this dog image and create 3 image prompts and 3 video prompts for: {description}"
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
                max_tokens=1200
            )
            
            response_text = response.choices[0].message.content.strip()
            print(f"OpenAI image+prompt response: {response_text[:300]}...")
            
            # JSON 마크다운 제거 및 파싱
            try:
                # ```json 및 ``` 제거
                clean_text = response_text
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]  # ```json 제거
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]   # ``` 제거
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]  # 끝의 ``` 제거
                clean_text = clean_text.strip()
                
                print(f"Cleaned JSON: {clean_text[:200]}...")
                
                result = json.loads(clean_text)
                dog_analysis = result.get("dog_analysis", {})
                image_prompts = result.get("image_prompts", [])
                video_prompts = result.get("video_prompts", [])
                
                if (isinstance(image_prompts, list) and isinstance(video_prompts, list) and 
                    len(image_prompts) == 3 and len(video_prompts) == 3 and
                    isinstance(dog_analysis, dict)):
                    return dog_analysis, image_prompts, video_prompts
                else:
                    print(f"Invalid response format, expected 3 image and 3 video prompts with dog analysis")
                    # Fallback: 기본 분석 후 3단계 생성
                    dog_analysis = await self.analyze_dog_image(dog_image_path)
                    fallback_img, fallback_vid = self._generate_fallback_video_sequence_with_images_test(description, content_type, dog_analysis)
                    return dog_analysis, fallback_img, fallback_vid
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                # Fallback: 기본 분석 후 3단계 생성
                dog_analysis = await self.analyze_dog_image(dog_image_path)
                fallback_img, fallback_vid = self._generate_fallback_video_sequence_with_images_test(description, content_type, dog_analysis)
                return dog_analysis, fallback_img, fallback_vid
                
        except Exception as e:
            print(f"Error in image+prompt generation: {e}")
            # Fallback: 기본 분석 후 3단계 생성
            dog_analysis = await self.analyze_dog_image(dog_image_path)
            fallback_img, fallback_vid = self._generate_fallback_video_sequence_with_images_test(description, content_type, dog_analysis)
            return dog_analysis, fallback_img, fallback_vid
    
    def _generate_fallback_video_sequence_with_images_test(self, description: str, content_type: str, dog_analysis: Dict) -> Tuple[List[str], List[str]]:
        """Fallback 3단계 이미지 + 비디오 시퀀스 생성 (테스트용)"""
        
        breed = dog_analysis.get('breed', 'dog')
        color = dog_analysis.get('color', 'brown')
        temperament = dog_analysis.get('temperament', 'playful')
        
        image_prompts = []
        video_prompts = []
        
        if "보호소" in description or "shelter" in description.lower():
            # 보호소 관련 시퀀스 (3단계)
            scenarios = [
                ("shelter entrance", "entering the animal shelter and looking around"),
                ("spotting camera", "noticing the camera and starting to run toward it"),
                ("running to camera", "running happily toward camera with joyful expression")
            ]
        else:
            # 일반적인 시퀀스 (3단계)
            scenarios = [
                ("beginning", f"starting {description}"),
                ("progress", f"actively engaged in {description}"),
                ("completion", f"successfully finishing {description} with satisfaction")
            ]
        
        for i, (scene, action) in enumerate(scenarios):
            # 이미지 프롬프트 (정적 장면)
            img_prompt = f"{breed} {temperament} {color} dog, {scene} scene: detailed view of {action}, high quality, realistic, well-lit"
            image_prompts.append(img_prompt)
            
            # 비디오 프롬프트 (움직임)
            vid_prompt = f"{breed} dog smoothly {action}, natural motion, cinematic view, expressive emotions"
            video_prompts.append(vid_prompt)
        
        return image_prompts, video_prompts

    async def select_best_image(self, image_paths: List[str], prompt: str, project_description: str) -> Tuple[int, str]:
        """3개 이미지 중 프롬프트에 가장 적합한 이미지 선택 (클래식 워크플로우용)"""
        
        if len(image_paths) <= 1:
            return 0, "Only one image available"
        
        try:
            # 이미지들을 base64로 인코딩
            image_data_list = []
            for i, image_path in enumerate(image_paths):
                try:
                    with open(image_path, "rb") as image_file:
                        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                        image_data_list.append({
                            "index": i,
                            "data": base64_image
                        })
                except Exception as e:
                    print(f"Error loading image {i}: {e}")
                    continue
            
            if not image_data_list:
                return 0, "No valid images found"
            
            # OpenAI Vision으로 이미지 분석 및 선택
            messages = [
                {
                    "role": "system",
                    "content": """You are an expert at selecting the best image for video generation.
Analyze the provided images and select the one that best matches the given prompt and project description.

Consider these criteria:
1. Visual quality and clarity
2. Composition and framing
3. Relevance to the prompt
4. Suitability for video animation
5. Overall aesthetic appeal

Respond with ONLY a JSON object in this format:
{
    "selected_index": 0,
    "reason": "Brief explanation of why this image is best"
}"""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Project: {project_description}\nPrompt: {prompt}\n\nSelect the best image from these {len(image_data_list)} options:"
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
                max_tokens=200
            )
            
            response_text = response.choices[0].message.content.strip()
            print(f"Image selection response: {response_text}")
            
            # JSON 마크다운 제거 및 파싱
            try:
                # ```json 및 ``` 제거
                clean_text = response_text
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]  # ```json 제거
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]   # ``` 제거
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]  # 끝의 ``` 제거
                clean_text = clean_text.strip()
                
                result = json.loads(clean_text)
                selected_index = result.get("selected_index", 0)
                reason = result.get("reason", "AI selected this image as most suitable")
                
                # 인덱스 유효성 검사
                if 0 <= selected_index < len(image_paths):
                    return selected_index, reason
                else:
                    return 0, f"Invalid index {selected_index}, using first image"
                    
            except json.JSONDecodeError:
                return 0, "Failed to parse selection response, using first image"
                
        except Exception as e:
            print(f"Error in image selection: {e}")
            return 0, f"Error during selection: {str(e)}, using first image"

    async def analyze_image_and_optimize_video_prompt(self, image_path: str, original_prompt: str, project_description: str, content_type: str) -> str:
        """선택된 이미지를 분석하여 비디오 프롬프트 최적화 (클래식 워크플로우용)"""
        
        try:
            # 이미지를 base64로 인코딩
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            messages = [
                {
                    "role": "system",
                    "content": f"""You are an expert at optimizing video generation prompts based on image analysis.

Analyze the provided image and optimize the video prompt to create the best possible video animation.

Consider:
1. Visual elements in the image (objects, composition, lighting)
2. Potential for natural movement and animation
3. Consistency with the original prompt intent
4. Content type: {content_type}
5. Project context: {project_description}

Create an optimized prompt that:
- Is 15-25 words long
- Describes specific, natural movements
- Works well with the image as a starting frame
- Maintains the original prompt's intent
- Uses cinematic language

Return ONLY the optimized prompt text, no explanation."""
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Original prompt: {original_prompt}\n\nOptimize this prompt based on the image:"
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
                max_tokens=150
            )
            
            optimized_prompt = response.choices[0].message.content.strip()
            
            # 기본 검증
            if len(optimized_prompt) < 10:
                return f"Smooth camera movement bringing to life: {original_prompt}"
            
            return optimized_prompt
            
        except Exception as e:
            print(f"Error optimizing video prompt: {e}")
            # Fallback: 원본 프롬프트에 기본 최적화 적용
            return f"Cinematic view with natural movement: {original_prompt}"

    async def generate_image_and_video_prompts(self, description: str, content_type: str) -> Tuple[List[str], List[str]]:
        """클래식 워크플로우용: 이미지 프롬프트와 비디오 프롬프트를 분리해서 생성"""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"""You are an expert at creating prompts for AI image and video generation.

Create exactly 10 image prompts and 10 corresponding video prompts based on the user's description.

Content Type: {content_type}
- If "life" (일상생활): Focus on daily life activities
- If "cooking" (요리): Focus on cooking and food preparation  
- If "travel" (여행): Focus on travel and exploration

Requirements:
1. Create 10 detailed image prompts that show different scenes/moments
2. Create 10 corresponding video prompts that animate those images
3. Image prompts should be static scenes, 15-25 words each
4. Video prompts should describe movement and animation, 15-25 words each
5. Both should work together as a cohesive sequence

Return ONLY a JSON object in this format:
{{
    "image_prompts": ["prompt1", "prompt2", ...],
    "video_prompts": ["prompt1", "prompt2", ...]
}}"""
                },
                {
                    "role": "user",
                    "content": f"Create 10 image prompts and 10 video prompts for: {description}"
                }
            ]
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            
            response_text = response.choices[0].message.content.strip()
            print(f"Generated prompts response: {response_text[:200]}...")
            
            # JSON 마크다운 제거 및 파싱
            try:
                # ```json 및 ``` 제거
                clean_text = response_text
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]  # ```json 제거
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]   # ``` 제거
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]  # 끝의 ``` 제거
                clean_text = clean_text.strip()
                
                result = json.loads(clean_text)
                image_prompts = result.get("image_prompts", [])
                video_prompts = result.get("video_prompts", [])
                
                if len(image_prompts) == 10 and len(video_prompts) == 10:
                    return image_prompts, video_prompts
                else:
                    print(f"Invalid prompt counts: {len(image_prompts)} image, {len(video_prompts)} video")
                    return self._generate_fallback_prompts(description, content_type)
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                return self._generate_fallback_prompts(description, content_type)
                
        except Exception as e:
            print(f"Error generating prompts: {e}")
            return self._generate_fallback_prompts(description, content_type)

    def _generate_fallback_prompts(self, description: str, content_type: str) -> Tuple[List[str], List[str]]:
        """Fallback 프롬프트 생성"""
        
        image_prompts = []
        video_prompts = []
        
        for i in range(10):
            step = i + 1
            
            # 이미지 프롬프트 (정적 장면)
            img_prompt = f"Scene {step}: detailed view of {description}, step {step}, high quality, realistic, well-lit"
            image_prompts.append(img_prompt)
            
            # 비디오 프롬프트 (움직임 추가)
            vid_prompt = f"Smooth camera movement showing {description}, step {step}, natural motion, cinematic view"
            video_prompts.append(vid_prompt)
        
        return image_prompts, video_prompts

    async def generate_image_and_video_prompts_with_custom_dog(self, description: str, dog_analysis: Dict, content_type: str) -> Tuple[List[str], List[str]]:
        """커스텀 강아지 기반 이미지와 비디오 프롬프트 생성"""
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"""You are an expert at creating prompts for AI image and video generation with custom dogs.

Create exactly 10 image prompts and 10 corresponding video prompts based on the user's description and the specific dog analysis.

Dog Analysis: {dog_analysis}
Content Type: {content_type}

Requirements:
1. Use the specific dog breed: {dog_analysis.get('breed', 'dog')}
2. Incorporate the dog's characteristics: {', '.join(dog_analysis.get('characteristics', []))}
3. Consider the dog's size: {dog_analysis.get('size', 'medium')}
4. Include the dog's color: {dog_analysis.get('color', 'brown')}
5. Match the dog's temperament: {dog_analysis.get('temperament', 'playful')}
6. Create 10 detailed image prompts (static scenes, 15-25 words each)
7. Create 10 corresponding video prompts (movement and animation, 15-25 words each)
8. Both should work together as a cohesive sequence

Return ONLY a JSON object in this format:
{{
    "image_prompts": ["prompt1", "prompt2", ...],
    "video_prompts": ["prompt1", "prompt2", ...]
}}"""
                },
                {
                    "role": "user",
                    "content": f"Create 10 image prompts and 10 video prompts for this {dog_analysis.get('breed', 'dog')}: {description}"
                }
            ]
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
            
            response_text = response.choices[0].message.content.strip()
            print(f"Generated custom dog prompts response: {response_text[:200]}...")
            
            # JSON 마크다운 제거 및 파싱
            try:
                # ```json 및 ``` 제거
                clean_text = response_text
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]  # ```json 제거
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]   # ``` 제거
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]  # 끝의 ``` 제거
                clean_text = clean_text.strip()
                
                result = json.loads(clean_text)
                image_prompts = result.get("image_prompts", [])
                video_prompts = result.get("video_prompts", [])
                
                if len(image_prompts) == 10 and len(video_prompts) == 10:
                    return image_prompts, video_prompts
                else:
                    print(f"Invalid prompt counts: {len(image_prompts)} image, {len(video_prompts)} video")
                    return self._generate_fallback_custom_dog_prompts(description, dog_analysis, content_type)
                    
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                return self._generate_fallback_custom_dog_prompts(description, dog_analysis, content_type)
                
        except Exception as e:
            print(f"Error generating custom dog prompts: {e}")
            return self._generate_fallback_custom_dog_prompts(description, dog_analysis, content_type)

    def _generate_fallback_custom_dog_prompts(self, description: str, dog_analysis: Dict, content_type: str) -> Tuple[List[str], List[str]]:
        """커스텀 강아지용 Fallback 프롬프트 생성"""
        
        breed = dog_analysis.get('breed', 'dog')
        color = dog_analysis.get('color', 'brown')
        size = dog_analysis.get('size', 'medium')
        
        image_prompts = []
        video_prompts = []
        
        for i in range(10):
            step = i + 1
            
            # 이미지 프롬프트 (정적 장면)
            img_prompt = f"{breed} {color} {size} dog, scene {step}: detailed view of {description}, step {step}, high quality, realistic"
            image_prompts.append(img_prompt)
            
            # 비디오 프롬프트 (움직임 추가)
            vid_prompt = f"{breed} dog smoothly performing {description}, step {step}, natural motion, cinematic view"
            video_prompts.append(vid_prompt)
        
        return image_prompts, video_prompts 