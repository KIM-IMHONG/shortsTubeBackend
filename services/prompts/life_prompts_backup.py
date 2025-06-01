# services/prompts/life_prompts.py
import re
from typing import Dict, Tuple, List

class LifePrompts:
    """일상 생활 YouTube Shorts 생성을 위한 프롬프트 템플릿"""
    
    @staticmethod
    def generate_life_image_prompt(description: str, dog_info: Dict[str, str] = None) -> str:
        """일상 활동 이미지 프롬프트 생성 - 영상의 첫 장면"""
        
        # 강아지 정보가 없으면 기본값 사용
        if not dog_info:
            dog_description = "friendly medium-sized dog"
        else:
            dog_description = dog_info.get('description', 'friendly dog')
        
        # 사용자가 입력한 설명을 그대로 사용하여 첫 장면 묘사
        image_prompt = f"""
        8K hyperrealistic photography, {dog_description}, {description}.
        
        Scene: First moment of the activity, dog is alert and engaged, natural posture, realistic proportions.
        
        Canon EOS R5, 35mm lens, natural lighting. Ultra-detailed fur texture, photorealistic environment. NO humans visible, only the dog.
        """.strip()
        
        return image_prompt

    @staticmethod
    def generate_life_video_prompt(description: str, dog_info: Dict[str, str] = None) -> str:
        """일상 활동 비디오 프롬프트 생성 - 행동 중심 간결하게"""
        
        # 강아지 정보
        if not dog_info:
            dog_description = "dog"
        else:
            dog_description = f"{dog_info.get('breed', 'dog')}"
        
        # 간결한 행동 중심 프롬프트
        video_prompt = f"""
        6-second: {dog_description} {description}.
        
        Action: Natural movement, realistic physics. Tail wagging, ears alert.
        
        Quality: 8K, stable camera, natural lighting.
        """.strip()
        
        return video_prompt

    @staticmethod
    def get_image_only_system_prompt():
        """일상 생활 이미지 프롬프트 시스템 - 10개 이미지 시퀀스"""
        return """
        You create HYPERREALISTIC daily life content featuring dogs in various everyday situations.
        
        The user will provide a SPECIFIC description of what the dog should be doing.
        Your job is to create a 10-image sequence that tells a complete story based on that description.
        
        IMAGE SEQUENCE REQUIREMENTS (10 SEQUENTIAL SCENES):
        1. ARRIVAL/START - Dog beginning the described activity
        2-3. EXPLORATION - Dog discovering and investigating 
        4-6. MAIN ACTIVITY - Core action sequence
        7-8. INTERACTION - Engaging with environment or objects
        9. CLIMAX - Peak moment of the activity
        10. CONCLUSION - Satisfied conclusion or completion
        
        QUALITY STANDARDS:
        - 8K hyperrealistic photography
        - Natural dog behavior and physics
        - Realistic environments and lighting
        - Clear sequential progression
        - NO humans visible (dog-only perspective)
        - Professional photography quality
        
        Generate exactly 10 images that tell a complete story based on the user's specific description.
        """

    @staticmethod
    def get_image_only_user_prompt_template(description: str):
        """일상 활동 이미지 프롬프트 템플릿 - 10개 시퀀스"""
        
        return f"""
        Create 10 SEQUENTIAL hyperrealistic images showing a dog's daily life activity:
        
        Activity: {description}
        
        Generate a 10-image story sequence that shows the complete progression of this specific activity:
        
        IMAGE_1: [Dog beginning the activity - establishing shot]
        IMAGE_2: [Dog exploring or investigating the situation]
        IMAGE_3: [Dog discovering something interesting related to the activity]
        IMAGE_4: [Dog actively starting the main action]
        IMAGE_5: [Dog fully engaged in the activity]
        IMAGE_6: [Dog continuing the activity with variation]
        IMAGE_7: [Dog interacting with environment/objects]
        IMAGE_8: [Dog showing emotion/reaction]
        IMAGE_9: [Peak moment or highlight of the activity]
        IMAGE_10: [Dog completing the activity or satisfied conclusion]
        
        Each image should:
        - Show clear progression from previous scene
        - Maintain consistent dog appearance
        - Use 8K hyperrealistic photography style
        - Focus on natural dog behavior
        - Exclude any humans from the scene
        - Accurately depict the specific activity described
        """

    @staticmethod
    def get_system_prompt():
        """일상 생활 이미지와 영상 통합 시스템 프롬프트"""
        return """
        You create HYPERREALISTIC daily life content featuring dogs in everyday situations.
        
        The user will provide SPECIFIC descriptions of what the dog should be doing.
        Create content based EXACTLY on what the user describes.
        
        SEQUENCE STRUCTURE (10 images + 2 videos):
        Images 1-3: Beginning and initial exploration
        Images 4-6: Main activity sequence
        Images 7-9: Interactions and highlights
        Image 10: Satisfying conclusion
        Video 1: Key action moment (from images 4-6)
        Video 2: Emotional highlight or conclusion
        
        VIDEO REQUIREMENTS:
        - 6-second clips focusing on specific actions
        - Natural movement and realistic physics
        - Clear, simple action descriptions
        - Stable camera, natural lighting
        
        QUALITY STANDARDS:
        ✅ 8K hyperrealistic photography
        ✅ Natural dog behavior
        ✅ Sequential storytelling
        ✅ Consistent character
        ❌ NO humans visible
        ❌ NO impossible physics
        ❌ NO cartoon elements
        
        Generate exactly 10 images + 2 videos based on the user's specific description.
        """

    @staticmethod
    def get_user_prompt_template(description: str):
        """일상 활동 통합 프롬프트 템플릿 - 10개 이미지 + 2개 영상"""
        
        return f"""
        Create 10 images + 2 videos showing: {description}
        
        Requirements:
        - Dog performing the exact activity described
        - 8K hyperrealistic photography
        - Clear sequential progression
        - Natural behavior and physics
        - NO humans visible
        
        Generate exactly 10 IMAGE + 2 VIDEO prompts that accurately depict this specific activity:
        
        IMAGE_1: [Dog beginning: {description}]
        IMAGE_2: [Dog exploring the environment]
        IMAGE_3: [Dog discovering next step]
        IMAGE_4: [Dog actively engaged in main action]
        IMAGE_5: [Dog continuing the activity]
        IMAGE_6: [Dog progressing further]
        IMAGE_7: [Dog interacting with objects/environment]
        IMAGE_8: [Dog showing emotional response]
        IMAGE_9: [Activity reaching peak moment]
        IMAGE_10: [Dog completing/satisfied with result]
        VIDEO_1: [6-second key action sequence]
        VIDEO_2: [6-second emotional or concluding moment]
        """

    @staticmethod
    def create_custom_dog_info(dog_analysis: Dict[str, str]) -> Dict[str, str]:
        """분석된 강아지 정보를 프롬프트 생성용 형식으로 변환"""
        return {
            'name': dog_analysis.get('breed', 'Mixed Breed'),
            'description': dog_analysis.get('description', 'friendly dog with unique characteristics'),
            'distinctive_features': dog_analysis.get('distinctive_features', 'alert expression and natural features'),
            'appearance': dog_analysis.get('description', 'medium-sized friendly dog')
        }

    @staticmethod
    def generate_image_prompts_with_custom_dog(description: str, dog_analysis: Dict[str, str]) -> str:
        """업로드된 강아지로 일상 활동 이미지 프롬프트 생성"""
        
        custom_dog_info = LifePrompts.create_custom_dog_info(dog_analysis)
        
        # 정확한 강아지 특징 포함
        breed_name = custom_dog_info['name']
        exact_appearance = custom_dog_info['description']
        unique_features = custom_dog_info['distinctive_features']
        
        # 사용자가 입력한 활동을 그대로 사용
        image_prompt = f"""
        8K hyperrealistic photography, THIS EXACT {breed_name}: {exact_appearance}, {description}.
        
        CRITICAL: Maintain exact appearance - {unique_features}. Natural behavior and authentic movement.
        
        Canon EOS R5, 35mm lens, natural lighting. Photorealistic environment. NO humans, only this specific dog.
        """.strip()
        
        return image_prompt

    @staticmethod
    def get_custom_dog_user_prompt_template(description: str, dog_analysis: Dict[str, str]):
        """업로드된 강아지 기반 일상 활동 프롬프트 템플릿"""
        
        custom_dog_info = LifePrompts.create_custom_dog_info(dog_analysis)
        
        return f"""
        Create 10 SEQUENTIAL daily life images + 2 action videos featuring this UPLOADED DOG performing: {description}
        
        UPLOADED DOG SPECIFICATIONS:
        - Exact Breed: {custom_dog_info['name']}
        - Physical Details: {custom_dog_info['description']}
        - Key Features: {custom_dog_info['distinctive_features']}
        
        REQUIREMENTS:
        - IDENTICAL dog appearance in ALL 10 images
        - Natural daily life activities as described
        - Sequential storytelling
        - Realistic behavior and physics
        - 8K hyperrealistic quality
        
        GENERATE 10 IMAGES + 2 VIDEOS showing this exact dog:
        
        IMAGE_1: [This exact dog starting: {description}]
        IMAGE_2: [This dog exploring/investigating]
        IMAGE_3: [This dog discovering next step]
        IMAGE_4: [This dog actively performing main action]
        IMAGE_5: [This dog continuing enthusiastically]
        IMAGE_6: [This dog progressing in activity]
        IMAGE_7: [This dog interacting with environment]
        IMAGE_8: [This dog showing happy expression]
        IMAGE_9: [This dog at activity highlight]
        IMAGE_10: [This dog satisfied with completion]
        VIDEO_1: [6-second: This dog performing key action]
        VIDEO_2: [6-second: This dog's emotional moment]
        """

    @staticmethod
    def get_custom_dog_system_prompt():
        """업로드된 강아지 기반 일상 활동 시스템 프롬프트"""
        return """
        You create HYPERREALISTIC daily life content featuring a SPECIFIC DOG from an uploaded image.
        
        CRITICAL SUCCESS FACTORS:
        1. EXACT CHARACTER CONSISTENCY - Use provided dog description in EVERY scene
        2. NATURAL BEHAVIOR - Realistic dog actions and movements
        3. SEQUENTIAL STORYTELLING - Each image follows logically
        4. FOLLOW USER'S DESCRIPTION - Create exactly what the user describes
        
        The user will provide specific activity descriptions. Follow them precisely.
        
        IMAGE SEQUENCE (1-10):
        - Beginning: Starting the activity (1-3)
        - Middle: Main activity progression (4-7)
        - End: Climax and conclusion (8-10)
        
        VIDEO REQUIREMENTS:
        - VIDEO 1: Key action moment (6 seconds)
        - VIDEO 2: Emotional highlight (6 seconds)
        
        CONSISTENCY RULES:
        ✅ SAME dog features in every image
        ✅ LOGICAL activity progression
        ✅ REALISTIC movements
        ✅ NATURAL environments
        ❌ NO humans anywhere
        ❌ NO impossible actions
        ❌ NO character changes
        
        Output exactly 10 images + 2 videos featuring the uploaded dog performing the described activity.
        """

    @staticmethod
    def create_action_focused_video_prompt(dog_analysis: Dict[str, str], activity_description: str) -> str:
        """업로드된 강아지 기반 행동 중심 비디오 프롬프트"""
        
        custom_dog_info = LifePrompts.create_custom_dog_info(dog_analysis)
        
        return f"""
        6-second: {custom_dog_info['description']} performing {activity_description}.
        
        Action: Natural movement with realistic physics. This dog's {custom_dog_info['distinctive_features']} clearly visible.
        
        Quality: 8K, natural lighting, realistic movement.
        """

    @staticmethod
    def get_improved_video_prompt(description: str) -> str:
        """설명 기반으로 개선된 비디오 프롬프트 생성"""
        
        return f"""
        6-second: Dog performing {description}.
        
        Action: Natural movement, realistic physics. Clear action progression.
        
        Quality: 8K, stable camera, natural lighting.
        """.strip() 