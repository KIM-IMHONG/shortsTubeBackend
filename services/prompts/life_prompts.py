# app/services/prompts/life_prompts.py
import os
import asyncio
from typing import List, Dict, Tuple, Optional
from ..openai_service import OpenAIService
from ..minimax_service import MinimaxService

class LifePromptsService:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.minimax_service = MinimaxService()
    
    async def execute_complete_workflow(self, image_path: str, description: str, num_steps: int = 5) -> Dict:
        """
        완전한 4단계 워크플로우 실행
        
        1. OpenAI Vision API로 사진+설명 → 단계별 프롬프트 생성
        2. Minimax API로 사진+프롬프트들 → 이미지들 생성
        3. OpenAI Vision API로 생성된 이미지들 분석 → 최적 이미지 선택 + 비디오 프롬프트 생성
        4. Minimax API로 선택된 이미지+비디오 프롬프트 → 비디오 생성
        
        Args:
            image_path: 업로드된 강아지 사진 경로
            description: 사용자 설명
            num_steps: 생성할 단계 수 (기본 5개)
            
        Returns:
            완전한 워크플로우 결과 딕셔너리
        """
        
        result = {
            "status": "processing",
            "step": 1,
            "step_prompts": [],
            "generated_images": [],
            "selected_image_index": 0,
            "selection_reason": "",
            "video_prompt": "",
            "final_video_path": None,
            "error": None
        }
        
        try:
            print("=" * 60)
            print("🚀 새로운 4단계 워크플로우 시작")
            print("=" * 60)
            
            # 1단계: 단계별 프롬프트 생성
            print("📝 1단계: 사진과 설명으로 단계별 프롬프트 생성 중...")
            step_prompts = await self.openai_service.generate_step_prompts_from_image_and_description(
                image_path, description, num_steps
            )
            
            if not step_prompts:
                raise Exception("1단계 실패: 단계별 프롬프트 생성 실패")
                
            result["step_prompts"] = step_prompts
            result["step"] = 2
            print(f"✅ 1단계 완료: {len(step_prompts)}개 프롬프트 생성")
            for i, prompt in enumerate(step_prompts):
                print(f"   {i+1}. {prompt}")
            
            # 2단계: 이미지 생성
            print("\n🎨 2단계: 참고 이미지와 프롬프트들로 이미지 생성 중...")
            generated_images = await self.minimax_service.generate_images_from_prompts_and_reference(
                step_prompts, image_path
            )
            
            if not generated_images:
                raise Exception("2단계 실패: 이미지 생성 실패")
                
            result["generated_images"] = generated_images
            result["step"] = 3
            print(f"✅ 2단계 완료: {len(generated_images)}개 이미지 생성")
            
            # 3단계: 최적 이미지 선택 및 비디오 프롬프트 생성
            print("\n🔍 3단계: OpenAI로 최적 이미지 선택 및 비디오 프롬프트 생성 중...")
            selected_index, selection_reason, video_prompt = await self.openai_service.select_best_image_and_create_video_prompt(
                generated_images, step_prompts, description, image_path
            )
            
            result["selected_image_index"] = selected_index
            result["selection_reason"] = selection_reason
            result["video_prompt"] = video_prompt
            result["step"] = 4
            print(f"✅ 3단계 완료:")
            print(f"   선택된 이미지: {selected_index + 1}번 ({os.path.basename(generated_images[selected_index])})")
            print(f"   선택 이유: {selection_reason}")
            print(f"   비디오 프롬프트: {video_prompt}")
            
            # 4단계: 비디오 생성
            print("\n🎬 4단계: 선택된 이미지와 프롬프트로 비디오 생성 중...")
            selected_image_path = generated_images[selected_index]
            final_video_path = await self.minimax_service.generate_video_from_image_and_prompt(
                selected_image_path, video_prompt
            )
            
            if not final_video_path:
                raise Exception("4단계 실패: 비디오 생성 실패")
                
            result["final_video_path"] = final_video_path
            result["status"] = "completed"
            result["step"] = 5
            
            print("=" * 60)
            print("🎉 4단계 워크플로우 완료!")
            print(f"📹 최종 비디오: {os.path.basename(final_video_path)}")
            print("=" * 60)
            
            return result
            
        except Exception as e:
            print(f"❌ 워크플로우 실패 (단계 {result['step']}): {e}")
            result["status"] = "failed"
            result["error"] = str(e)
            return result
    
    async def execute_step_by_step(self, image_path: str, description: str, step: int, previous_data: Optional[Dict] = None, num_steps: int = 5) -> Dict:
        """
        단계별 실행 (개별 단계별로 호출 가능)
        
        Args:
            image_path: 업로드된 강아지 사진 경로
            description: 사용자 설명
            step: 실행할 단계 (1-4)
            previous_data: 이전 단계의 결과 데이터
            num_steps: 생성할 단계 수
            
        Returns:
            해당 단계의 결과 딕셔너리
        """
        
        try:
            if step == 1:
                # 1단계: 단계별 프롬프트 생성
                print(f"📝 1단계 실행: 단계별 프롬프트 생성 ({num_steps}개)")
                step_prompts = await self.openai_service.generate_step_prompts_from_image_and_description(
                    image_path, description, num_steps
                )
                
                return {
                    "status": "success",
                    "step": 1,
                    "data": {
                        "step_prompts": step_prompts,
                        "count": len(step_prompts)
                    }
                }
                
            elif step == 2:
                # 2단계: 이미지 생성
                if not previous_data or "step_prompts" not in previous_data:
                    return {"status": "error", "message": "1단계 데이터가 필요합니다"}
                
                print(f"🎨 2단계 실행: 이미지 생성 ({len(previous_data['step_prompts'])}개)")
                generated_images = await self.minimax_service.generate_images_from_prompts_and_reference(
                    previous_data["step_prompts"], image_path
                )
                
                return {
                    "status": "success",
                    "step": 2,
                    "data": {
                        "generated_images": generated_images,
                        "count": len(generated_images)
                    }
                }
                
            elif step == 3:
                # 3단계: 이미지 선택 및 비디오 프롬프트 생성
                if not previous_data or "generated_images" not in previous_data or "step_prompts" not in previous_data:
                    return {"status": "error", "message": "1-2단계 데이터가 필요합니다"}
                
                print("🔍 3단계 실행: 최적 이미지 선택 및 비디오 프롬프트 생성")
                selected_index, selection_reason, video_prompt = await self.openai_service.select_best_image_and_create_video_prompt(
                    previous_data["generated_images"], previous_data["step_prompts"], description, image_path
                )
                
                return {
                    "status": "success",
                    "step": 3,
                    "data": {
                        "selected_image_index": selected_index,
                        "selected_image_path": previous_data["generated_images"][selected_index],
                        "selection_reason": selection_reason,
                        "video_prompt": video_prompt
                    }
                }
                
            elif step == 4:
                # 4단계: 비디오 생성
                if not previous_data or "selected_image_path" not in previous_data or "video_prompt" not in previous_data:
                    return {"status": "error", "message": "1-3단계 데이터가 필요합니다"}
                
                print("🎬 4단계 실행: 비디오 생성")
                final_video_path = await self.minimax_service.generate_video_from_image_and_prompt(
                    previous_data["selected_image_path"], previous_data["video_prompt"]
                )
                
                if not final_video_path:
                    return {"status": "error", "message": "비디오 생성 실패"}
                
                return {
                    "status": "success",
                    "step": 4,
                    "data": {
                        "final_video_path": final_video_path
                    }
                }
                
            else:
                return {"status": "error", "message": f"유효하지 않은 단계: {step} (1-4만 가능)"}
                
        except Exception as e:
            return {
                "status": "error",
                "step": step,
                "message": str(e)
            } 