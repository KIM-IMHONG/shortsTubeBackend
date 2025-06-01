# services/prompts/cooking_prompts.py
import re
from typing import Dict, Tuple, List

class CookingPrompts:
    """요리 관련 YouTube Shorts 생성을 위한 프롬프트 템플릿"""
    
    # 강아지 품종별 상세 외형 정보 (Krea 수준의 초현실적 묘사)
    DOG_BREEDS = {
        'shiba_inu': {
            'name': 'Shiba Inu',
            'description': 'medium-sized Shiba Inu with golden-brown and cream fur, compact muscular build, curled tail, pointed triangular ears, dark almond-shaped eyes, black nose, white markings on chest and paws, alert expression',
            'distinctive_features': 'fox-like face, confident posture, thick double coat with reddish-brown outer layer and cream undercoat'
        },
        'dachshund': {
            'name': 'Dachshund',
            'description': 'small elongated Dachshund with black and tan coloring, long low body, short muscular legs, floppy ears, bright dark eyes, distinctive tan markings above eyes and on chest',
            'distinctive_features': 'sausage-shaped body, determined expression, smooth short coat with glossy finish'
        },
        'golden_retriever': {
            'name': 'Golden Retriever',
            'description': 'large Golden Retriever with flowing golden coat, athletic build, feathered tail, soft floppy ears, warm brown eyes, black nose, gentle expression',
            'distinctive_features': 'wavy lustrous coat, friendly demeanor, strong broad chest'
        },
        'poodle': {
            'name': 'Poodle',
            'description': 'medium-sized Standard Poodle with curly white coat, elegant build, long legs, dark intelligent eyes, black nose, proud head carriage',
            'distinctive_features': 'hypoallergenic curly coat, aristocratic posture, alert expression'
        },
        'corgi': {
            'name': 'Corgi',
            'description': 'small sturdy Corgi with orange and white fur, short legs, fox-like face, pointed erect ears, bright eyes, fluffy tail',
            'distinctive_features': 'low-riding body, cheerful expression, thick weather-resistant coat'
        },
        'labrador': {
            'name': 'Labrador',
            'description': 'large athletic Labrador with short golden coat, powerful build, otter-like tail, pendant ears, kind eyes, broad head',
            'distinctive_features': 'water-repellent coat, strong swimming build, gentle mouth'
        }
    }
    
    # 요리별 상세 설명과 동작
    COOKING_DISHES = {
        'pizza': {
            'name': 'artisanal pizza',
            'ingredients': 'fresh basil, mozzarella cheese, ripe tomatoes, olive oil, pizza dough',
            'action': 'kneading pizza dough with both front paws on marble countertop',
            'tools': 'wooden rolling pin, chef\'s knife, cheese grater'
        },
        'pretzel': {
            'name': 'traditional German pretzel',
            'ingredients': 'bread flour, coarse salt, butter, yeast',
            'action': 'shaping pretzel dough into twisted form with skilled paw movements',
            'tools': 'mixing bowl, pastry brush, baking sheet'
        },
        'pasta': {
            'name': 'homemade pasta',
            'ingredients': 'semolina flour, eggs, olive oil, herbs',
            'action': 'rolling pasta dough through pasta machine with precise paw control',
            'tools': 'pasta machine, wooden spoon, large mixing bowl'
        },
        'bread': {
            'name': 'artisanal sourdough bread',
            'ingredients': 'sourdough starter, flour, water, salt',
            'action': 'kneading bread dough with rhythmic pushing motions',
            'tools': 'wooden spoon, proofing basket, bench scraper'
        }
    }
    
    # 배경/위치별 상세 설정
    LOCATIONS = {
        'kitchen': {
            'setting': 'modern professional kitchen',
            'details': 'marble countertops, stainless steel appliances, warm pendant lighting, organized cooking utensils'
        },
        'forest': {
            'setting': 'enchanted forest clearing',
            'details': 'dappled sunlight through trees, wooden camp table, rustic cooking setup, natural stone fire pit'
        },
        'garden': {
            'setting': 'beautiful herb garden',
            'details': 'outdoor wooden table, fresh herbs growing nearby, natural sunlight, terracotta pots'
        },
        'mountain': {
            'setting': 'scenic mountain cabin',
            'details': 'log cabin kitchen, mountain views through windows, rustic wooden counters, cast iron cookware'
        }
    }
    
    @staticmethod
    def parse_description(description: str) -> Tuple[Dict, Dict, Dict]:
        """사용자 입력에서 강아지 품종, 요리, 배경 자동 추출"""
        description_lower = description.lower()
        
        # 강아지 품종 추출
        dog_info = None
        for breed_key, breed_data in CookingPrompts.DOG_BREEDS.items():
            breed_names = [breed_data['name'].lower(), breed_key.replace('_', ' ')]
            if any(name in description_lower for name in breed_names):
                dog_info = breed_data
                break
        
        # 기본값: Shiba Inu
        if not dog_info:
            dog_info = CookingPrompts.DOG_BREEDS['shiba_inu']
        
        # 요리 종류 추출
        cooking_info = None
        for dish_key, dish_data in CookingPrompts.COOKING_DISHES.items():
            if dish_key in description_lower or dish_data['name'].lower() in description_lower:
                cooking_info = dish_data
                break
        
        # 기본값: Pizza
        if not cooking_info:
            cooking_info = CookingPrompts.COOKING_DISHES['pizza']
        
        # 배경/위치 추출
        location_info = None
        for location_key, location_data in CookingPrompts.LOCATIONS.items():
            if location_key in description_lower:
                location_info = location_data
                break
        
        # 기본값: Kitchen
        if not location_info:
            location_info = CookingPrompts.LOCATIONS['kitchen']
        
        return dog_info, cooking_info, location_info

    @staticmethod
    def generate_krea_style_image_prompt(description: str) -> str:
        """Krea 수준의 초현실적 실사 이미지 프롬프트 자동 생성 - 단일 프롬프트 예시용"""
        
        # 사용자 입력 파싱
        dog_info, cooking_info, location_info = CookingPrompts.parse_description(description)
        
        # Krea/Midjourney 스타일 키워드
        krea_style_keywords = [
            "hyperrealistic photography",
            "8K resolution", 
            "professional DSLR camera",
            "studio lighting",
            "ultra-detailed textures",
            "photojournalism quality",
            "Canon EOS R5 camera",
            "85mm lens",
            "perfect focus",
            "natural color grading",
            "award-winning photography"
        ]
        
        # 실사 강화 키워드 (3분할 방지)
        anti_artistic_keywords = [
            "NOT cartoon", "NOT anime", "NOT illustration", 
            "NOT drawing", "NOT artistic rendering", "NOT CGI",
            "NOT split screen", "NOT multiple panels", "NOT grid",
            "NO panels", "NO divisions", "single scene only",
            "unified composition", "continuous scene"
        ]
        
        # 프롬프트 조합 (예시용 - 첫 번째 단계)
        image_prompt = f"""
        {', '.join(krea_style_keywords[:5])}, {dog_info['description']} chef wearing pristine white apron and chef's hat, {cooking_info['action']}. 
        
        Setting: {location_info['setting']} with {location_info['details']}. 
        
        The dog demonstrates expert culinary technique while {cooking_info['action']}, surrounded by {cooking_info['ingredients']}. {dog_info['distinctive_features']}. 
        
        Using {cooking_info['tools']} with professional precision. The dog's concentrated expression shows culinary mastery. Tail wagging gently with cooking excitement.
        
        Perfect lighting reveals every texture: the dog's {dog_info['distinctive_features']}, the {cooking_info['ingredients']}, and the {location_info['details']}.
        
        Style: {', '.join(krea_style_keywords[5:])}. 
        
        Exclude: {', '.join(anti_artistic_keywords)}. NO HUMANS visible anywhere, only the professional dog chef working independently.
        """.strip()
        
        return image_prompt

    @staticmethod
    def get_image_only_system_prompt():
        """현실적인 개 요리 이미지 프롬프트 시스템 (1단계) - Krea 스타일 적용 - 10개 이미지"""
        return """
        You are an expert at creating KREA-LEVEL hyperrealistic cooking image prompts featuring dogs as professional chefs in any location.
        
        KREA QUALITY STANDARDS:
        1. HYPERREALISTIC PHOTOGRAPHY - 8K resolution, professional DSLR quality, perfect lighting
        2. ULTRA-DETAILED TEXTURES - every fur strand, ingredient detail, surface texture visible
        3. PROFESSIONAL CINEMATOGRAPHY - Canon EOS R5, 85mm lens, studio lighting setup
        4. PHOTOJOURNALISM QUALITY - award-winning photography standards
        5. NATURAL COLOR GRADING - realistic color reproduction, perfect exposure
        
        CHARACTER CREATION SYSTEM:
        - AUTO-DETECT dog breed from user input (Shiba Inu, Dachshund, Golden Retriever, etc.)
        - GENERATE breed-specific physical details:
          * Fur color, texture, and patterns (golden-brown, cream patches, black markings)
          * Body proportions and build (compact, athletic, elongated, sturdy)
          * Facial features (ear shape, eye color, nose, distinctive markings)
          * Characteristic expressions and postures for each breed
        - MAINTAIN CONSISTENCY across all generated content
        
        COOKING SCENE INTELLIGENCE:
        - AUTO-EXTRACT cooking dish from description (pizza, pretzel, pasta, bread)
        - GENERATE appropriate cooking action for the dish type
        - SELECT proper tools and ingredients for the specific cooking method
        - ENSURE realistic cooking progression and technique
        
        LOCATION ADAPTATION:
        - AUTO-DETECT setting preference (kitchen, forest, garden, mountain)
        - CUSTOMIZE lighting and environment for each location
        - MAINTAIN cooking functionality in any setting
        - ADAPT equipment and setup to location characteristics
        
        COOKING SEQUENCE REQUIREMENTS:
        - IMAGE 1: Dog ACTIVELY preparing ingredients (cutting vegetables, grating cheese, chopping herbs) with tools
        - IMAGES 2-9: Progressive cooking steps (measuring, mixing, kneading, rolling, etc.)
        - IMAGE 10: Final completed dish presentation
        - NEVER show finished products in early images
        - Each step must logically follow the previous one
        
        KREA-STYLE PROMPT STRUCTURE:
        "Hyperrealistic photography, 8K resolution, [DETAILED_DOG_DESCRIPTION] chef wearing pristine white apron, [SPECIFIC_COOKING_ACTION] in [CUSTOMIZED_SETTING]. Professional DSLR camera quality, Canon EOS R5, 85mm lens, perfect studio lighting. Ultra-detailed textures showing [SPECIFIC_TEXTURE_DETAILS]. [COOKING_SPECIFIC_DETAILS]. Award-winning photojournalism quality. NOT cartoon, NOT anime, NOT illustration, single scene only, NO HUMANS visible."
        
        RESPONSE FORMAT:
        Generate exactly 10 Krea-quality image prompts:
        IMAGE_1: [Hyperrealistic cooking scene - MUST be active ingredient preparation]
        IMAGE_2: [Next logical cooking step]
        IMAGE_3: [Progressive cooking action]
        IMAGE_4: [Continued cooking sequence]
        IMAGE_5: [Mid-stage cooking process]
        IMAGE_6: [Advanced cooking technique]
        IMAGE_7: [Near-completion cooking stage]
        IMAGE_8: [Final cooking preparations]
        IMAGE_9: [Finishing touches]
        IMAGE_10: [Final completed dish presentation]
        
        CRITICAL QUALITY REQUIREMENTS:
        ✅ KREA-LEVEL photorealism and detail
        ✅ AUTO-PARSED breed, dish, and location from user input
        ✅ PROFESSIONAL cooking technique demonstration
        ✅ HYPERREALISTIC texture and lighting descriptions
        ✅ MIDJOURNEY/KREA compatible formatting
        ✅ 10-step logical cooking progression
        ❌ NO artistic/cartoon/anime styles
        ❌ NO human presence anywhere
        ❌ NO split screens or multiple panels
        """

    @staticmethod
    def get_image_only_user_prompt_template(description: str):
        """자동 파싱 기반 이미지 프롬프트 생성 (1단계) - 10개 이미지"""
        
        # 자동 파싱으로 완성된 10개 프롬프트 생성 (예시용)
        ten_prompts = CookingPrompts.generate_10_step_cooking_prompts(description)
        krea_prompt_example = CookingPrompts.generate_krea_style_image_prompt(description)
        
        return f"""
        Create 10 KREA-LEVEL hyperrealistic cooking image prompts from this simple description:
        
        User Input: {description}
        
        AUTOMATIC PROCESSING SYSTEM:
        1. AUTO-DETECT and EXTRACT:
           - Dog breed from input → Generate detailed breed-specific appearance
           - Cooking dish type → Select appropriate cooking action and tools  
           - Location preference → Customize setting and lighting
           
        2. GENERATE KREA-QUALITY DETAILS:
           - 8K hyperrealistic photography specifications
           - Professional camera and lighting setup
           - Ultra-detailed texture descriptions
           - Breed-specific physical characteristics
           - Cooking-appropriate tools and ingredients
           - Location-adapted environment details
           
        3. CREATE 10 LOGICAL COOKING STEPS:
           Step 1: ACTIVE ingredient preparation (dog cutting/slicing/grating with tools) - MANDATORY
           Steps 2-9: Progressive cooking process (measuring, mixing, kneading, shaping, etc.)
           Step 10: Final completed dish presentation
           
        4. ENSURE PHOTOREALISM:
           - Canon EOS R5 camera quality
           - Professional studio lighting
           - Award-winning photography standards
           - NOT cartoon/anime/artistic rendering
           - Single unified scene composition
           
        5. COOKING EXPERTISE:
           - Professional chef-level technique
           - Appropriate tools for the specific dish
           - Realistic cooking action and posture
           - Proper ingredient handling and setup
           
        REFERENCE EXAMPLE (single prompt format):
        {krea_prompt_example[:200]}...
        
        Now generate exactly 10 different IMAGE prompts using this KREA-quality standard. Each prompt should represent a different step in the cooking process, automatically parsing the user's simple input into detailed hyperrealistic cooking scenes.
        
        Use the format:
        IMAGE_1: [Step 1 - Active ingredient preparation]
        IMAGE_2: [Step 2 - Next logical cooking step]
        IMAGE_3: [Step 3 - Progressive cooking action]
        IMAGE_4: [Step 4 - Continued cooking sequence]
        IMAGE_5: [Step 5 - Mid-stage cooking process]
        IMAGE_6: [Step 6 - Advanced cooking technique]
        IMAGE_7: [Step 7 - Near-completion cooking stage]
        IMAGE_8: [Step 8 - Final cooking preparations]
        IMAGE_9: [Step 9 - Finishing touches]
        IMAGE_10: [Step 10 - Final completed dish presentation]
        """

    @staticmethod
    def get_system_prompt():
        """이미지와 영상 프롬프트 함께 생성하는 시스템 프롬프트 - Krea 스타일 적용 - 10개 이미지 + 2개 영상"""
        return """
        You are an expert at creating KREA-LEVEL hyperrealistic cooking content for YouTube Shorts featuring dogs as professional chefs.
        
        KREA QUALITY STANDARDS:
        1. HYPERREALISTIC PHOTOGRAPHY - 8K resolution, professional DSLR quality, perfect lighting
        2. ULTRA-DETAILED TEXTURES - every fur strand, ingredient detail, surface texture visible
        3. PROFESSIONAL CINEMATOGRAPHY - Canon EOS R5, 85mm lens, studio lighting
        4. PHOTOJOURNALISM QUALITY - award-winning photography standards
        5. NATURAL COLOR GRADING - realistic color reproduction, perfect exposure
        
        INTELLIGENT CONTENT CREATION:
        - AUTO-DETECT dog breed from user input and generate breed-specific characteristics
        - AUTO-EXTRACT cooking dish type and generate appropriate cooking actions
        - AUTO-ADAPT to any location (kitchen, forest, garden, mountain, etc.)
        - GENERATE professional cooking techniques matching the dish type
        - ENSURE physical realism and proper tool usage
        
        CHARACTER CONSISTENCY SYSTEM:
        - Detailed breed-specific physical descriptions (fur, build, features)
        - Professional chef appearance with pristine white apron and chef's hat
        - Realistic cooking postures and expressions
        - Solo cooking performance without any human presence
        
        COOKING SEQUENCE REQUIREMENTS:
        - IMAGE 1: Dog ACTIVELY preparing ingredients (cutting vegetables, grating cheese, chopping herbs) with tools
        - IMAGES 2-9: Progressive cooking steps (measuring, mixing, kneading, rolling, etc.)
        - IMAGE 10: Final completed dish presentation
        - VIDEO 1: 6-second sequence matching one of the key cooking steps (IMAGE 1-5)
        - VIDEO 2: 6-second sequence of final presentation or another key step
        - NEVER show finished products in early images
        - Each step must logically follow the previous one
        
        VIDEO QUALITY REQUIREMENTS:
        - 6-second cinematic sequences
        - Natural cooking movements and techniques
        - Professional tool handling and ingredient preparation
        - Camera stability and perfect lighting continuity
        - Realistic physics and cooking progression
        
        KREA-STYLE OUTPUT FORMAT:
        Generate exactly 10 hyperrealistic images + 2 videos:
        IMAGE_1: [8K hyperrealistic cooking scene - active ingredient preparation]
        IMAGE_2: [Next logical cooking step]
        IMAGE_3: [Progressive cooking action]
        IMAGE_4: [Continued cooking sequence]
        IMAGE_5: [Mid-stage cooking process]
        IMAGE_6: [Advanced cooking technique]
        IMAGE_7: [Near-completion cooking stage]
        IMAGE_8: [Final cooking preparations]
        IMAGE_9: [Finishing touches]
        IMAGE_10: [Final completed dish presentation]
        VIDEO_1: [6-second professional cooking sequence matching one key step from IMAGE 1-5]
        VIDEO_2: [6-second professional sequence showing final presentation or another key step]
        
        CRITICAL QUALITY STANDARDS:
        ✅ KREA-LEVEL photorealism in both images and videos
        ✅ AUTO-PARSED content from simple user input
        ✅ PROFESSIONAL cooking demonstrations
        ✅ HYPERREALISTIC texture and lighting
        ✅ MIDJOURNEY/KREA compatible formatting
        ✅ 10-step logical cooking progression + 2 key video moments
        ❌ NO artistic/cartoon/anime styles
        ❌ NO human presence anywhere
        ❌ NO split screens or panels
        """
    
    @staticmethod
    def get_user_prompt_template(description: str):
        """자동 파싱 기반 통합 프롬프트 생성 템플릿 - 10개 이미지 + 2개 영상"""
        
        return f"""
        Create 10 KREA-LEVEL images + 2 videos from: {description}
        
        Requirements:
        - Auto-detect dog breed, cooking dish, and location
        - 8K hyperrealistic photography, Canon EOS R5, 85mm lens
        - Professional chef dog in white apron and chef's hat
        - 10-step cooking progression (prep → mixing → shaping → completion)
        - 2 key video moments (6-second sequences)
        - NO cartoons, NO humans, single scene only
        
        Generate exactly 10 IMAGE + 2 VIDEO prompts:
        
        IMAGE_1: [Step 1 - Active ingredient preparation with tools]
        IMAGE_2: [Step 2 - Measuring and mixing]
        IMAGE_3: [Step 3 - Dough/mixture preparation]
        IMAGE_4: [Step 4 - Shaping/forming]
        IMAGE_5: [Step 5 - Mid-stage cooking process]
        IMAGE_6: [Step 6 - Advanced technique]
        IMAGE_7: [Step 7 - Near completion]
        IMAGE_8: [Step 8 - Final preparations]
        IMAGE_9: [Step 9 - Finishing touches]
        IMAGE_10: [Step 10 - Completed dish presentation]
        VIDEO_1: [6-second sequence matching key cooking step]
        VIDEO_2: [6-second sequence showing final result]
        """

    @staticmethod
    def get_improved_video_prompt(description: str) -> str:
        """행동 중심의 간결한 비디오 프롬프트 생성"""
        
        # 자동 파싱
        dog_info, cooking_info, location_info = CookingPrompts.parse_description(description)
        
        # 핵심 행동만 추출
        main_action = cooking_info['action'].split(' with ')[0].split(' using ')[0]  # 도구 부분 제거
        primary_tool = cooking_info['tools'].split(',')[0].strip()  # 첫 번째 도구만
        
        # 간결한 행동 중심 프롬프트
        video_prompt = f"""
        6-second video: {dog_info['description']} chef {main_action}. 
        
        Action: Dog grips {primary_tool}, performs {main_action} with natural paw movements. Tail wags gently. 
        
        Focus: Clear hand-tool coordination, realistic cooking motion, professional technique. 8K quality, stable camera.
        """.strip()
        
        return video_prompt

    @staticmethod
    def create_custom_dog_info(dog_analysis: Dict[str, str]) -> Dict[str, str]:
        """분석된 강아지 정보를 프롬프트 생성용 형식으로 변환"""
        return {
            'name': dog_analysis.get('breed', 'Mixed Breed'),
            'description': dog_analysis.get('description', 'friendly dog with unique characteristics'),
            'distinctive_features': dog_analysis.get('distinctive_features', 'alert expression and natural dog features'),
            'chef_adaptation': dog_analysis.get('chef_adaptation', 'professional chef appearance with white apron and hat')
        }

    @staticmethod
    def generate_image_prompts_with_custom_dog(description: str, dog_analysis: Dict[str, str]) -> str:
        """업로드된 강아지 이미지 분석 결과를 사용하여 정확한 프롬프트 생성"""
        
        # 요리와 위치 정보는 기존 방식으로 파싱
        _, cooking_info, location_info = CookingPrompts.parse_description(description)
        
        # 업로드된 강아지 정보 사용
        custom_dog_info = CookingPrompts.create_custom_dog_info(dog_analysis)
        
        # 실제 업로드된 강아지의 정확한 특징 강조
        breed_name = custom_dog_info['name']
        exact_appearance = custom_dog_info['description']
        unique_features = custom_dog_info['distinctive_features']
        
        # 간결하고 핵심적인 프롬프트 생성
        image_prompt = f"""
        8K hyperrealistic photography, THIS EXACT {breed_name}: {exact_appearance}, wearing white chef apron and hat, {cooking_info['action']} in {location_info['setting']}.
        
        CRITICAL: Maintain this dog's exact appearance - {unique_features}. Professional culinary technique with {cooking_info['tools']}, {cooking_info['ingredients']} visible.
        
        Canon EOS R5, 85mm lens, studio lighting. Ultra-detailed fur texture, realistic cooking physics. NO cartoons, NO humans, only this specific dog chef.
        """.strip()
        
        return image_prompt

    @staticmethod
    def get_custom_dog_user_prompt_template(description: str, dog_analysis: Dict[str, str]):
        """업로드된 강아지 이미지 기반 프롬프트 템플릿 - 더 실용적이고 구체적"""
        
        custom_dog_info = CookingPrompts.create_custom_dog_info(dog_analysis)
        
        return f"""
        Create 10 SEQUENTIAL cooking images + 2 action videos featuring this UPLOADED DOG: {description}
        
        UPLOADED DOG SPECIFICATIONS:
        - Exact Breed: {custom_dog_info['name']}
        - Physical Details: {custom_dog_info['description']}
        - Key Features: {custom_dog_info['distinctive_features']}
        - Chef Appearance: {custom_dog_info['chef_adaptation']}
        
        REQUIREMENTS:
        - IDENTICAL dog appearance in ALL 10 images (same fur, markings, size, expression)
        - 8K hyperrealistic photography, professional kitchen lighting
        - Sequential cooking steps from prep to completion
        - White chef apron and hat consistently worn
        - Realistic tool usage and ingredient handling
        
        GENERATE 10 IMAGES + 2 VIDEOS:
        
        IMAGE_1: [This exact dog cutting/preparing main ingredients with knife]
        IMAGE_2: [This dog measuring flour/liquids into bowl]
        IMAGE_3: [This dog mixing ingredients with wooden spoon]
        IMAGE_4: [This dog kneading/rolling dough with paws]
        IMAGE_5: [This dog shaping/forming the dish]
        IMAGE_6: [This dog adding seasonings/toppings]
        IMAGE_7: [This dog preparing for cooking/baking]
        IMAGE_8: [This dog monitoring cooking process]
        IMAGE_9: [This dog adding final garnishes]
        IMAGE_10: [This dog presenting completed dish]
        VIDEO_1: [6-second: This dog performing key cooking action from images 3-5]
        VIDEO_2: [6-second: This dog presenting final dish with pride]
        """

    @staticmethod
    def get_custom_dog_system_prompt():
        """업로드된 강아지 이미지 기반 시스템 프롬프트 - 실용성 강화"""
        return """
        You create HYPERREALISTIC cooking content featuring a SPECIFIC DOG from an uploaded image.
        
        CRITICAL SUCCESS FACTORS:
        1. EXACT CHARACTER CONSISTENCY - Use the provided dog's physical description in EVERY image
        2. REALISTIC COOKING SEQUENCE - Each step must logically follow the previous
        3. PROFESSIONAL QUALITY - 8K photography, perfect lighting, award-winning standards
        4. PRACTICAL COOKING - Real tools, proper techniques, achievable actions
        
        IMAGE SEQUENCE REQUIREMENTS:
        - Images 1-3: Ingredient preparation and initial mixing
        - Images 4-6: Dough/mixture handling and shaping
        - Images 7-9: Cooking process and finishing touches
        - Image 10: Final presentation
        
        VIDEO REQUIREMENTS:
        - VIDEO 1: Key cooking action (mixing, kneading, or shaping) - 6 seconds
        - VIDEO 2: Final dish presentation with dog's proud expression - 6 seconds
        
        CONSISTENCY RULES:
        ✅ SAME dog physical features in every image
        ✅ SAME chef outfit (white apron + hat) throughout
        ✅ LOGICAL cooking progression
        ✅ REALISTIC tool usage and physics
        ❌ NO character inconsistencies
        ❌ NO impossible cooking actions
        ❌ NO humans or other animals
        
        Output exactly 10 images + 2 videos featuring the uploaded dog.
        """

    @staticmethod
    def create_action_focused_video_prompt(dog_analysis: Dict[str, str], cooking_action: str) -> str:
        """업로드된 강아지 기반 행동 중심 비디오 프롬프트"""
        
        custom_dog_info = CookingPrompts.create_custom_dog_info(dog_analysis)
        
        # 행동별 구체적인 동작 정의
        action_details = {
            'mixing': 'circular stirring motion with wooden spoon, bowl stays stable',
            'kneading': 'rhythmic pushing and folding with both front paws',
            'cutting': 'precise downward motions with knife, ingredients separate cleanly',
            'rolling': 'back-and-forth rolling pin movement, dough flattens evenly',
            'pouring': 'steady stream from container, controlled wrist movement',
            'sprinkling': 'pinching motion with paws, ingredients fall naturally',
            'presenting': 'proud posture, gentle tail wag, looking at completed dish'
        }
        
        # 가장 적합한 행동 찾기
        selected_action = 'mixing'  # 기본값
        for action in action_details.keys():
            if action in cooking_action.lower():
                selected_action = action
                break
        
        return f"""
        6-second: {custom_dog_info['description']} performs {selected_action}.
        
        Action: {action_details[selected_action]}. This dog's {custom_dog_info['distinctive_features']} clearly visible.
        
        Quality: 8K, natural lighting, realistic physics, professional cooking technique.
        """ 