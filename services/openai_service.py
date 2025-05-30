# app/services/openai_service.py
from openai import OpenAI
from typing import List, Dict, Tuple
import asyncio
import os
import re

class OpenAIService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
        
    async def generate_prompts(self, description: str) -> Tuple[List[str], List[str]]:
        """Generate synchronized image and video prompts based on user description"""
        
        # API 키가 없으면 에러 발생
        if not self.client:
            raise RuntimeError("OPENAI_API_KEY not set in environment variables")
        
        system_prompt = """
        You are an expert at creating perfectly synchronized and CONTINUOUS IMAGE and VIDEO prompts for YouTube Shorts cooking videos.
        
        CRITICAL RULE: NEVER use reference expressions! Each prompt must be COMPLETELY SELF-CONTAINED.
        
        PROHIBITED WORDS/PHRASES:
        - "Identical background", "Same background", "Consistent background"
        - "Same character", "Identical character", "Consistent character"
        - "Previous step", "From step 2", "Step 2 results"
        - "Same setup", "Identical setup", "Consistent setup"
        - Any reference to previous prompts or scenes
        
        REQUIRED: Every single prompt must contain the COMPLETE description:
        
        FULL BACKGROUND (COPY EXACTLY IN ALL PROMPTS):
        "Modern rustic kitchen with white subway tile backsplash, warm oak wooden countertops throughout, stainless steel appliances in background, large window on left side providing natural daylight, wooden cutting board as main work surface in center, mixing bowls and utensils positioned consistently, camera positioned at counter level with slight downward angle, consistent warm lighting from natural light plus warm kitchen overhead lights"
        
        CHARACTER DESCRIPTION RULES:
        - Extract the main character from user description (dog, cat, person, etc.)
        - Add cooking attire: white chef's hat and apron
        - Specify positioning: standing at counter height or on stool if needed
        - Include realistic detail keywords
        - For animals: emphasize "NOT HUMAN, ONLY [ANIMAL]"
        
        WORKSPACE LAYOUT (COPY EXACTLY IN ALL PROMPTS):
        "Large mixing bowl center-left of wooden cutting board, ingredients arranged in small bowls on right side, cooking tools available on right side, consistent spatial layout"
        
        COOKING PROGRESSION RULES:
        - Extract the dish/recipe from user description
        - Create logical 10-step cooking progression for that specific dish
        - Each step should be realistic and sequential
        - Adapt ingredients and tools to match the specific recipe
        
        PROMPT STRUCTURE RULES:
        
        IMAGE PROMPTS = STATIC FIRST FRAME ONLY:
        - Describe exactly what is visible at the START of each step
        - Show the current state of ingredients, tools, character position
        - NO movement, NO actions, just the frozen moment before action begins
        - Focus on: positioning, ingredients state, character pose, facial expression
        
        VIDEO PROMPTS = MOVEMENT FROM THAT STATE:
        - Describe HOW the character moves from the static state shown in image
        - Specify the exact action/movement that brings the scene to life
        - Include camera movement if needed
        - Focus on: hand movements, head movements, ingredient transformations, motion dynamics
        
        CRITICAL VIDEO PROMPT REQUIREMENTS:
        - ALWAYS specify which body parts are moving (two front paws, left paw, right paw, head, etc.)
        - CLEARLY state what object the body part is interacting with (spoon, bowl, dough, etc.)
        - DESCRIBE the result of the action (dough gets mixed, ingredients combine, etc.)
        - USE action verbs: grabs, stirs, kneads, pours, lifts, pushes, rolls, etc.
        
        VIDEO PROMPT EXAMPLES:
        ❌ BAD: "HOW the dog mixes the ingredients"
        ✅ GOOD: "HOW the dog uses both front paws to grab the wooden spoon handle, then moves the spoon in circular motions clockwise inside the bowl while the flour and water combine into dough"
        
        ❌ BAD: "HOW the dog kneads the dough"  
        ✅ GOOD: "HOW the dog presses down on the dough with both front paws alternately, pushing and folding the dough while it becomes smooth and elastic under the paw pressure"
        
        ❌ BAD: "HOW the dog shapes pretzels"
        ✅ GOOD: "HOW the dog uses both front paws to roll the dough into long rope, then carefully twists the rope into pretzel shape by crossing the ends and folding them down"
        
        SYNCHRONIZATION: Each IMAGE-VIDEO pair describes the SAME moment - image shows the static starting state, video shows the movement from that exact state.
        """
        
        user_prompt = f"""
        Based on the following description, generate exactly 10 perfectly synchronized and CONTINUOUS IMAGE-VIDEO pairs in English:
        {description}
        
        **MANDATORY REQUIREMENTS:**
        
        1. EVERY prompt must start with COMPLETE descriptions (no shortcuts or references)
        2. Copy the EXACT background and workspace descriptions in ALL 20 prompts
        3. Extract the CHARACTER from user description and create consistent character description
        4. Extract the DISH/RECIPE from user description and create logical 10-step progression
        5. IMAGE prompts = STATIC FIRST FRAME only (no movement, no actions)
        6. VIDEO prompts = SPECIFIC MOVEMENT from that static state
        
        **TEMPLATE STRUCTURE TO FOLLOW:**
        
        For each IMAGE prompt:
        [FULL BACKGROUND] + [CONSISTENT CHARACTER DESCRIPTION] + [WORKSPACE LAYOUT] + [Step X STATIC STATE: specific ingredients/tools visible, character position and expression] + [Ultra-realistic photograph, professional studio lighting, DSLR camera quality, Canon EOS R5, 85mm lens, sharp focus, NOT cartoon, NOT anime, NOT illustration, single scene, NOT split screen, NOT multiple panels, NOT grid]
        
        For each VIDEO prompt:
        [FULL BACKGROUND] + [CONSISTENT CHARACTER DESCRIPTION] + [HOW the character moves from that static state - SPECIFIC BODY PARTS and ACTIONS with RESULTS]
        
        **CRITICAL VIDEO PROMPT RULES:**
        - Always specify exact body parts: "both front paws", "left paw", "right paw", "head", etc.
        - State what tool/object is being used: spoon, bowl, dough, rolling pin, etc.  
        - Describe the movement direction: clockwise, back and forth, up and down, side to side
        - Show the result: dough mixes, ingredients combine, shape changes, etc.
        
        VIDEO PROMPT STRUCTURE: "HOW the [CHARACTER] uses [SPECIFIC BODY PART] to [GRAB/HOLD] the [TOOL], then [SPECIFIC MOVEMENT DIRECTION] while [VISIBLE RESULT OCCURS]"
        
        **IMPORTANT INSTRUCTIONS:**
        
        Character Creation:
        - If animal: Add "wearing white chef's hat and blue apron, standing on stool at counter height, NOT HUMAN, ONLY [ANIMAL TYPE]"
        - If human: Add "wearing white chef's hat and blue apron, standing at counter height"
        - Keep character description IDENTICAL in all 20 prompts
        
        Recipe Progression:
        - Create realistic 10-step cooking sequence for the specific dish mentioned
        - Step 1: Preparation/ingredient setup
        - Steps 2-8: Main cooking process (mixing, shaping, cooking, etc.)
        - Step 9: Finishing touches
        - Step 10: Single completed dish moment (NOT presentation, just one specific frozen moment)
        
        CRITICAL FOR ALL IMAGES: Include anti-split keywords to prevent multi-panel generation
        ESPECIALLY for final images: NO "presentation", "display", "showcase", "final result" keywords
        
        Remember: 
        - IMAGE = What you see in the frozen first frame (static state)
        - VIDEO = How that scene moves and comes to life (specific actions)
        - NO reference words, COMPLETE descriptions in every prompt!
        - Character and dish must match user's description exactly
        
        **EXACT OUTPUT FORMAT REQUIRED:**
        
        IMAGE_1: [your image prompt here]
        VIDEO_1: [your video prompt here]
        IMAGE_2: [your image prompt here]
        VIDEO_2: [your video prompt here]
        ...continue through IMAGE_10 and VIDEO_10
        
        DO NOT use any other format. Start each line with exactly "IMAGE_1:", "VIDEO_1:", etc.
        """
        
        try:
            print("🚀 Calling OpenAI API...")
            print(f"Model: gpt-4.1")
            print(f"Temperature: 0.3")
            print(f"Max tokens: 8192")
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4.1",  # 2025년 최신 모델 - 지시사항 준수 87.4% (업계 최고), 코딩 특화, 100만 토큰 컨텍스트
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # 일관된 스토리텔링을 위한 최적 설정
                max_tokens=8192  # 상세한 프롬프트 20개 생성을 위해 토큰 제한 대폭 증가
            )
            
            print("✅ OpenAI API call successful")
            
            # 응답 완성도 확인
            finish_reason = response.choices[0].finish_reason
            print(f"Finish reason: {finish_reason}")
            
            if finish_reason == "length":
                print("⚠️  WARNING: Response was truncated due to token limit!")
                print("Consider increasing max_tokens further if parsing fails.")
            elif finish_reason != "stop":
                print(f"⚠️  WARNING: Unexpected finish reason: {finish_reason}")
            
            # 토큰 사용량 확인
            if hasattr(response, 'usage') and response.usage:
                print(f"Token usage - Prompt: {response.usage.prompt_tokens}, Completion: {response.usage.completion_tokens}, Total: {response.usage.total_tokens}")
            
            # 응답 구조 확인
            if not response or not response.choices:
                raise RuntimeError("Empty response from OpenAI API")
            
            if not response.choices[0].message:
                raise RuntimeError("No message in OpenAI response")
            
            content = response.choices[0].message.content
            
            if not content:
                raise RuntimeError("Empty content in OpenAI response")
            
            # 응답 파싱
            print(f"Raw response length: {len(content)}")
            print(f"Raw response (first 1000 chars):\n{content[:1000]}")  # 더 많은 디버깅 정보
            print(f"Raw response (last 500 chars):\n{content[-500:]}")  # 끝 부분도 확인
            
            image_prompts = []
            video_prompts = []
            
            # 더 강건한 파싱
            lines = content.strip().split('\n')
            print(f"Total lines in response: {len(lines)}")
            
            # 각 라인 확인 (디버깅용)
            for i, line in enumerate(lines[:20]):  # 처음 20줄만 출력
                if line.strip():
                    print(f"Line {i}: {line.strip()[:100]}")
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # IMAGE_X: 형식 파싱 (더 넓은 범위 확인)
                if ("IMAGE" in line.upper() and ":" in line):
                    try:
                        # 다양한 형식 지원
                        if line.upper().startswith("**IMAGE"):
                            # **IMAGE_1:** 형식
                            clean_line = line.replace("**", "").replace("*", "")
                            image_prompt = clean_line.split(":", 1)[1].strip()
                        elif line.upper().startswith("IMAGE"):
                            # IMAGE_1: 형식
                            image_prompt = line.split(":", 1)[1].strip()
                        elif "IMAGE" in line.upper() and ":" in line:
                            # 기타 형식 (중간에 IMAGE가 있는 경우)
                            parts = line.split(":")
                            if len(parts) >= 2:
                                image_prompt = ":".join(parts[1:]).strip()
                            else:
                                continue
                        else:
                            continue
                            
                        if image_prompt:  # 빈 문자열이 아닌 경우만
                            image_prompts.append(image_prompt)
                            print(f"Found image prompt {len(image_prompts)}: {image_prompt[:100]}...")
                    except Exception as ex:
                        print(f"Error parsing image line: {line[:100]} - {ex}")
                        pass
                
                # VIDEO_X: 형식 파싱 (더 넓은 범위 확인)
                elif ("VIDEO" in line.upper() and ":" in line):
                    try:
                        # 다양한 형식 지원
                        if line.upper().startswith("**VIDEO"):
                            # **VIDEO_1:** 형식
                            clean_line = line.replace("**", "").replace("*", "")
                            video_prompt = clean_line.split(":", 1)[1].strip()
                        elif line.upper().startswith("VIDEO"):
                            # VIDEO_1: 형식
                            video_prompt = line.split(":", 1)[1].strip()
                        elif "VIDEO" in line.upper() and ":" in line:
                            # 기타 형식 (중간에 VIDEO가 있는 경우)
                            parts = line.split(":")
                            if len(parts) >= 2:
                                video_prompt = ":".join(parts[1:]).strip()
                            else:
                                continue
                        else:
                            continue
                            
                        if video_prompt:  # 빈 문자열이 아닌 경우만
                            video_prompts.append(video_prompt)
                            print(f"Found video prompt {len(video_prompts)}: {video_prompt[:100]}...")
                    except Exception as ex:
                        print(f"Error parsing video line: {line[:100]} - {ex}")
                        pass
            
            # 10개 확인
            if len(image_prompts) != 10 or len(video_prompts) != 10:
                print(f"❌ Parsing error - Image prompts: {len(image_prompts)}, Video prompts: {len(video_prompts)}")
                print("Retrying with simpler parsing...")
                
                # 재시도: 번호로 정렬된 프롬프트 찾기
                image_prompts = []
                video_prompts = []
                
                for i in range(1, 11):  # 10개
                    img_found = False
                    vid_found = False
                    
                    for line in lines:
                        line_upper = line.upper()
                        # **IMAGE_i:** 또는 IMAGE_i: 형식 모두 확인
                        if not img_found and (f"IMAGE_{i}:" in line_upper or f"IMAGE {i}:" in line_upper):
                            try:
                                if "**" in line:
                                    clean_line = line.replace("**", "").replace("*", "")
                                    prompt = clean_line.split(":", 1)[1].strip()
                                else:
                                    prompt = line.split(":", 1)[1].strip()
                                if prompt:
                                    image_prompts.append(prompt)
                                    img_found = True
                                    print(f"✅ Found IMAGE_{i}: {prompt[:50]}...")
                            except Exception as ex:
                                print(f"❌ Error parsing IMAGE_{i}: {ex}")
                                
                        # **VIDEO_i:** 또는 VIDEO_i: 형식 모두 확인  
                        elif not vid_found and (f"VIDEO_{i}:" in line_upper or f"VIDEO {i}:" in line_upper):
                            try:
                                if "**" in line:
                                    clean_line = line.replace("**", "").replace("*", "")
                                    prompt = clean_line.split(":", 1)[1].strip()
                                else:
                                    prompt = line.split(":", 1)[1].strip()
                                if prompt:
                                    video_prompts.append(prompt)
                                    vid_found = True
                                    print(f"✅ Found VIDEO_{i}: {prompt[:50]}...")
                            except Exception as ex:
                                print(f"❌ Error parsing VIDEO_{i}: {ex}")
                
                print(f"🔄 Fallback parsing result - Images: {len(image_prompts)}, Videos: {len(video_prompts)}")
                
                # 여전히 실패한 경우, 더 공격적인 파싱 시도
                if len(image_prompts) != 10 or len(video_prompts) != 10:
                    print("🔄 Trying aggressive parsing...")
                    
                    # 전체 텍스트에서 IMAGE와 VIDEO 패턴 찾기
                    image_patterns = re.findall(r'IMAGE[_\s]*(\d+)[:\s]*(.+?)(?=VIDEO|IMAGE|\n\n|$)', content, re.IGNORECASE | re.DOTALL)
                    video_patterns = re.findall(r'VIDEO[_\s]*(\d+)[:\s]*(.+?)(?=IMAGE|VIDEO|\n\n|$)', content, re.IGNORECASE | re.DOTALL)
                    
                    print(f"📝 Regex found - Image patterns: {len(image_patterns)}, Video patterns: {len(video_patterns)}")
                    
                    if image_patterns:
                        image_prompts = [pattern[1].strip() for pattern in sorted(image_patterns, key=lambda x: int(x[0]))][:10]
                    if video_patterns:
                        video_prompts = [pattern[1].strip() for pattern in sorted(video_patterns, key=lambda x: int(x[0]))][:10]
                
                if len(image_prompts) != 10 or len(video_prompts) != 10:
                    # 최종 에러 - 상세한 디버깅 정보 출력
                    print("💀 FINAL PARSING FAILURE - DETAILED DEBUG INFO:")
                    print(f"Total lines: {len(lines)}")
                    print("All non-empty lines:")
                    for i, line in enumerate(lines):
                        if line.strip():
                            print(f"Line {i:3d}: {line.strip()}")
                    print("="*80)
                    
                    raise ValueError(f"Expected 10 prompts each, but got {len(image_prompts)} images and {len(video_prompts)} videos")
            
            # 생성된 프롬프트 로깅 - 동기화 확인
            print("Generated synchronized English prompts:")
            for i in range(10):
                print(f"\n=== PAIR {i+1} (Same Action) ===")
                print(f"IMAGE: {image_prompts[i][:200]}...")
                print(f"VIDEO: {video_prompts[i][:200]}...")
                
            return image_prompts, video_prompts
            
        except Exception as e:
            print(f"OpenAI API Error: {str(e)}")
            raise  # 에러를 그대로 전파
    
    # 기존 메서드들은 제거 또는 수정
    async def generate_image_prompts(self, description: str) -> List[str]:
        """하위 호환성을 위한 래퍼 메서드"""
        image_prompts, _ = await self.generate_prompts(description)
        return image_prompts 