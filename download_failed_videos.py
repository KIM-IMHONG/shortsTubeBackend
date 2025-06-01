#!/usr/bin/env python3
import asyncio
import aiohttp
import os
import json
from services.minimax_service import MinimaxService

async def download_failed_videos():
    """실패한 비디오들을 file_id로 다운로드"""
    
    # 로그에서 확인된 모든 file_id들 (0-10번)
    failed_videos = [
        # 7번과 8번은 이미 다운로드 완료했지만 다시 시도
        {
            "file_id": "274927369957561",
            "description": "video_7 - 강아지가 무인계산기 앞에서 신나하는 모습",
            "video_number": 7
        },
        {
            "file_id": "274929455358122", 
            "description": "video_8 - 강아지가 화면을 보며 꼬리 흔드는 모습",
            "video_number": 8
        },
        # 9번과 10번 추가
        {
            "file_id": "274932497686670",
            "description": "video_9 - 강아지가 발로 화면을 터치하여 구매 완료",
            "video_number": 9
        },
        {
            "file_id": "274929942106215",
            "description": "video_10 - 강아지가 가방에 물건을 담고 기쁘게 매장을 나가는 모습",
            "video_number": 10
        }
    ]
    
    print(f"🔄 Downloading {len(failed_videos)} videos...")
    print(f"📝 Note: 0-6번 비디오의 file_id는 별도로 확인이 필요합니다.")
    
    minimax_service = MinimaxService()
    
    for i, video_info in enumerate(failed_videos):
        file_id = video_info["file_id"]
        description = video_info["description"]
        video_number = video_info["video_number"]
        
        print(f"\n📥 Downloading video {i+1}/{len(failed_videos)} (Video #{video_number})")
        print(f"📄 File ID: {file_id}")
        print(f"📝 Description: {description}")
        
        # 이미 다운로드된 파일이 있는지 확인
        existing_file = f"recovered_video_{video_number}_{file_id}.mp4"
        existing_path = os.path.join("downloads/videos", existing_file)
        
        if os.path.exists(existing_path):
            print(f"✅ Already downloaded: {existing_file}")
            continue
        
        try:
            async with aiohttp.ClientSession() as session:
                # file_id를 URL로 변환
                print(f"🔗 Getting download URL...")
                download_url = await minimax_service._get_file_url(session, file_id)
                
                if download_url:
                    print(f"✅ Download URL obtained: {download_url[:100]}...")
                    
                    # 비디오 다운로드
                    video_filename = f"recovered_video_{video_number}_{file_id}.mp4"
                    video_path = await minimax_service._download_single_video(session, download_url, video_filename)
                    
                    if video_path:
                        print(f"🎉 Successfully downloaded: {os.path.basename(video_path)}")
                    else:
                        print(f"❌ Failed to download video")
                else:
                    print(f"❌ Failed to get download URL for file_id: {file_id}")
                    
        except Exception as e:
            print(f"❌ Error downloading video {video_number}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✅ Download recovery process completed!")
    print(f"\n📋 다음 단계:")
    print(f"   1. 0-6번 비디오의 file_id를 로그에서 찾아서 추가해주세요")
    print(f"   2. 또는 새로운 프로젝트를 생성하여 전체 10개 비디오를 다시 생성해보세요")

async def find_missing_file_ids():
    """0-6번 비디오의 file_id를 찾기 위한 도우미 함수"""
    print("\n🔍 0-6번 비디오의 file_id를 찾기 위해서는:")
    print("   1. 백엔드 로그에서 task_id들을 확인하세요")
    print("   2. 각 task_id에 대해 Minimax API로 상태를 확인하세요")
    print("   3. Success 상태인 task들에서 file_id를 추출하세요")
    
    # 예시 task_id들 (로그에서 확인 가능한 것들)
    example_task_ids = [
        "274930302533772",  # video_7용
        "274930302533778",  # video_8용  
        "274928665366648",  # video_9용
        "274929942106215",  # video_10용
    ]
    
    print(f"\n💡 확인된 task_id 예시들:")
    for task_id in example_task_ids:
        print(f"   - {task_id}")

if __name__ == "__main__":
    asyncio.run(download_failed_videos())
    # asyncio.run(find_missing_file_ids()) 