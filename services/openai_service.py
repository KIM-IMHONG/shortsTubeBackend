# app/services/openai_service.py
from openai import OpenAI
from typing import List, Dict, Tuple
import asyncio
import os

class OpenAIService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
        
    async def generate_prompts(self, description: str) -> Tuple[List[str], List[str]]:
        """사용자 설명을 바탕으로 이미지와 비디오 프롬프트 동시 생성"""
        
        # API 키가 없으면 에러 발생
        if not self.client:
            raise RuntimeError("OPENAI_API_KEY not set in environment variables")
        
        system_prompt = """
        당신은 YouTube Shorts를 위한 이미지와 비디오 생성 전문가입니다.
        주어진 설명을 바탕으로 정확히 10개의 이미지 프롬프트와 대응하는 비디오 프롬프트를 생성해주세요.
        
        중요한 규칙:
        1. 반드시 영어로만 작성
        2. 주인공 캐릭터의 일관성이 가장 중요함:
           - 첫 프롬프트에서 캐릭터를 매우 구체적으로 설명
           - 모든 프롬프트에서 동일한 외형 특징 반복 (품종, 색상, 크기, 특징적인 표시)
           - 옷이나 액세서리가 있다면 모든 장면에서 동일하게 유지
        3. 인간의 손이나 신체 부위가 나타나지 않도록 명시
        4. 캐릭터가 실제로 행동하는 장면 묘사 (단순히 보고만 있지 않도록)
        5. 배경과 소품의 일관성 유지
        6. 각 장면은 독립적으로 이해 가능하면서도 전체 스토리의 일부
        """
        
        user_prompt = f"""
        다음 설명을 바탕으로 정확히 10개의 이미지 프롬프트와 비디오 프롬프트를 생성해주세요:
        {description}
        
        반드시 아래 형식을 정확히 따라주세요. 각 번호마다 IMAGE와 VIDEO 라인이 있어야 합니다:
        
        IMAGE_1: [이미지 프롬프트]
        VIDEO_1: [비디오 프롬프트]
        
        IMAGE_2: [이미지 프롬프트]
        VIDEO_2: [비디오 프롬프트]
        
        IMAGE_3: [이미지 프롬프트]
        VIDEO_3: [비디오 프롬프트]
        
        IMAGE_4: [이미지 프롬프트]
        VIDEO_4: [비디오 프롬프트]
        
        IMAGE_5: [이미지 프롬프트]
        VIDEO_5: [비디오 프롬프트]
        
        IMAGE_6: [이미지 프롬프트]
        VIDEO_6: [비디오 프롬프트]
        
        IMAGE_7: [이미지 프롬프트]
        VIDEO_7: [비디오 프롬프트]
        
        IMAGE_8: [이미지 프롬프트]
        VIDEO_8: [비디오 프롬프트]
        
        IMAGE_9: [이미지 프롬프트]
        VIDEO_9: [비디오 프롬프트]
        
        IMAGE_10: [이미지 프롬프트]
        VIDEO_10: [비디오 프롬프트]
        
        이미지 프롬프트 규칙:
        - 캐릭터의 전체 모습, 구체적인 외형 특징 포함
        - "no human hands or body parts visible" 명시
        - 캐릭터가 구체적인 동작을 하는 중인 장면
        
        비디오 프롬프트 규칙:
        - 해당 이미지에서 어떤 움직임이 일어날지 설명
        - 카메라 움직임과 캐릭터 동작 포함
        - 6초 동안의 자연스러운 움직임
        """
        
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=3000  # 토큰 수 증가
            )
            
            # 응답 파싱
            content = response.choices[0].message.content
            print(f"Raw response:\n{content[:500]}...")  # 디버깅용
            
            image_prompts = []
            video_prompts = []
            
            # 더 강건한 파싱
            lines = content.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # IMAGE_X: 형식 파싱
                if line.startswith("IMAGE_") and ":" in line:
                    try:
                        image_prompt = line.split(":", 1)[1].strip()
                        if image_prompt:  # 빈 문자열이 아닌 경우만
                            image_prompts.append(image_prompt)
                    except:
                        pass
                
                # VIDEO_X: 형식 파싱
                elif line.startswith("VIDEO_") and ":" in line:
                    try:
                        video_prompt = line.split(":", 1)[1].strip()
                        if video_prompt:  # 빈 문자열이 아닌 경우만
                            video_prompts.append(video_prompt)
                    except:
                        pass
            
            # 10개 확인
            if len(image_prompts) != 10 or len(video_prompts) != 10:
                print(f"Parsing error - Image prompts: {len(image_prompts)}, Video prompts: {len(video_prompts)}")
                print("Retrying with simpler parsing...")
                
                # 재시도: 번호로 정렬된 프롬프트 찾기
                image_prompts = []
                video_prompts = []
                
                for i in range(1, 11):
                    img_found = False
                    vid_found = False
                    
                    for line in lines:
                        if line.startswith(f"IMAGE_{i}:") and not img_found:
                            prompt = line.split(":", 1)[1].strip()
                            image_prompts.append(prompt)
                            img_found = True
                        elif line.startswith(f"VIDEO_{i}:") and not vid_found:
                            prompt = line.split(":", 1)[1].strip()
                            video_prompts.append(prompt)
                            vid_found = True
                
                if len(image_prompts) != 10 or len(video_prompts) != 10:
                    raise ValueError(f"Expected 10 prompts each, but got {len(image_prompts)} images and {len(video_prompts)} videos")
            
            # 생성된 프롬프트 로깅
            print("Generated prompts:")
            for i in range(10):
                print(f"\nScene {i+1}:")
                print(f"Image: {image_prompts[i][:100]}...")
                print(f"Video: {video_prompts[i][:100]}...")
                
            return image_prompts, video_prompts
            
        except Exception as e:
            print(f"OpenAI API Error: {str(e)}")
            raise  # 에러를 그대로 전파
    
    # 기존 메서드들은 제거 또는 수정
    async def generate_image_prompts(self, description: str) -> List[str]:
        """하위 호환성을 위한 래퍼 메서드"""
        image_prompts, _ = await self.generate_prompts(description)
        return image_prompts