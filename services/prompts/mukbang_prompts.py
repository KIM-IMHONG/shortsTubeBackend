# services/prompts/mukbang_prompts.py

class MukbangPrompts:
    """먹방 관련 YouTube Shorts 생성을 위한 프롬프트 템플릿 (향후 구현 예정)"""
    
    @staticmethod
    def get_system_prompt():
        # TODO: 먹방 시나리오에 특화된 시스템 프롬프트 구현
        return """
        Mukbang prompt system to be implemented.
        This will handle eating shows, food reviews, taste tests, etc.
        """
    
    @staticmethod
    def get_user_prompt_template(description: str):
        # TODO: 먹방 시나리오에 특화된 사용자 프롬프트 템플릿 구현
        return f"""
        Mukbang user prompt template to be implemented for: {description}
        """ 