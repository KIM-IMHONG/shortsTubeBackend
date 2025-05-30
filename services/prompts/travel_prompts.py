# services/prompts/travel_prompts.py

class TravelPrompts:
    """여행 관련 YouTube Shorts 생성을 위한 프롬프트 템플릿 (향후 구현 예정)"""
    
    @staticmethod
    def get_system_prompt():
        # TODO: 여행 시나리오에 특화된 시스템 프롬프트 구현
        return """
        Travel prompt system to be implemented.
        This will handle travel scenarios like sightseeing, hiking, city tours, etc.
        """
    
    @staticmethod
    def get_user_prompt_template(description: str):
        # TODO: 여행 시나리오에 특화된 사용자 프롬프트 템플릿 구현
        return f"""
        Travel user prompt template to be implemented for: {description}
        """ 