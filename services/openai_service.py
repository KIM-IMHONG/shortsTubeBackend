# app/services/openai_service.py
from openai import OpenAI
from typing import List, Dict, Tuple
import asyncio
import os
import re

# 프롬프트 모듈 임포트 (상대/절대 임포트 모두 지원)
try:
    from .prompts.cooking_prompts import CookingPrompts
    from .prompts.travel_prompts import TravelPrompts
    from .prompts.mukbang_prompts import MukbangPrompts
except ImportError:
    from prompts.cooking_prompts import CookingPrompts
    from prompts.travel_prompts import TravelPrompts
    from prompts.mukbang_prompts import MukbangPrompts

class OpenAIService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
            
        # 프롬프트 타입 매핑
        self.prompt_handlers = {
            'cooking': CookingPrompts,
            'travel': TravelPrompts,
            'mukbang': MukbangPrompts
        }
        
    async def generate_prompts(self, description: str, content_type: str = 'cooking') -> Tuple[List[str], List[str]]:
        """Generate synchronized image and video prompts based on user description and content type"""
        
        # API 키가 없으면 에러 발생
        if not self.client:
            raise RuntimeError("OPENAI_API_KEY not set in environment variables")
        
        # 콘텐츠 타입 검증
        if content_type not in self.prompt_handlers:
            available_types = ', '.join(self.prompt_handlers.keys())
            raise ValueError(f"Unsupported content type: {content_type}. Available types: {available_types}")
        
        # 해당 타입의 프롬프트 핸들러 가져오기
        prompt_handler = self.prompt_handlers[content_type]
        
        # 시스템 및 사용자 프롬프트 생성
        system_prompt = prompt_handler.get_system_prompt()
        user_prompt = prompt_handler.get_user_prompt_template(description)
        
        try:
            print(f"🚀 Calling OpenAI API for content type: {content_type}")
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
            
            print(f"✅ OpenAI API call successful for {content_type}")
            
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
            print(f"Generated synchronized {content_type} prompts:")
            for i in range(10):
                print(f"\n=== PAIR {i+1} (Same Action) ===")
                print(f"IMAGE: {image_prompts[i][:200]}...")
                print(f"VIDEO: {video_prompts[i][:200]}...")
                
            return image_prompts, video_prompts
            
        except Exception as e:
            print(f"OpenAI API Error: {str(e)}")
            raise  # 에러를 그대로 전파
    
    # 하위 호환성을 위한 래퍼 메서드들
    async def generate_image_prompts(self, description: str, content_type: str = 'cooking') -> List[str]:
        """하위 호환성을 위한 래퍼 메서드"""
        image_prompts, _ = await self.generate_prompts(description, content_type)
        return image_prompts 
    
    def get_available_content_types(self) -> List[str]:
        """사용 가능한 콘텐츠 타입 목록 반환"""
        return list(self.prompt_handlers.keys()) 