#!/usr/bin/env python3
import asyncio
import aiohttp
import os
import json
from services.minimax_service import MinimaxService

async def find_and_download_missing_videos():
    """로그에서 확인된 task_id들로 0-6번 비디오의 file_id를 찾고 다운로드"""
    
    # 로그에서 보이는 task_id들 (0-6번에 해당할 것으로 추정)
    # 실제로는 더 많은 task_id가 있을 수 있으니 사용자가 제공해야 함
    potential_task_ids = [
        # 여기에 0-6번 비디오의 task_id들을 추가해야 합니다
        # 로그에서 확인 가능한 task_id 패턴:
        # 예: "274930302533772", "274930302533778", "274928665366648", "274929942106215"
    ]
    
    print(f"🔍 0-6번 비디오의 file_id를 찾기 위한 방법들:")
    print(f"📝 현재 확인된 비디오 상황:")
    print(f"   ✅ Video 7: file_id 274927369957561 (다운로드 완료)")
    print(f"   ✅ Video 8: file_id 274929455358122 (다운로드 완료)")  
    print(f"   ✅ Video 9: file_id 274932497686670 (다운로드 완료)")
    print(f"   ❌ Video 10: file_id 274929942106215 (파일 없음)")
    print(f"   ❓ Video 0-6: file_id 확인 필요")
    
    minimax_service = MinimaxService()
    
    # 만약 task_id들이 있다면 확인해보기
    if potential_task_ids:
        print(f"\n🔄 Checking {len(potential_task_ids)} potential task_ids...")
        
        for i, task_id in enumerate(potential_task_ids):
            try:
                async with aiohttp.ClientSession() as session:
                    print(f"\n📊 Checking task_id {i+1}/{len(potential_task_ids)}: {task_id}")
                    
                    # Minimax API로 task 상태 확인
                    check_url = f"https://api.minimaxi.chat/v1/query/video_generation"
                    headers = {
                        "Authorization": f"Bearer {minimax_service.api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    async with session.get(
                        check_url,
                        params={"task_id": task_id},
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            print(f"   📄 Status: {result.get('status', 'unknown')}")
                            
                            if result.get('status') == 'Success' and 'file_id' in result:
                                file_id = result['file_id']
                                if file_id:
                                    print(f"   ✅ Found file_id: {file_id}")
                                    
                                    # 즉시 다운로드 시도
                                    download_url = await minimax_service._get_file_url(session, file_id)
                                    if download_url:
                                        video_filename = f"recovered_video_{i}_{file_id}.mp4"
                                        video_path = await minimax_service._download_single_video(
                                            session, download_url, video_filename
                                        )
                                        if video_path:
                                            print(f"   🎉 Downloaded: {os.path.basename(video_path)}")
                                else:
                                    print(f"   ❌ No file_id in successful task")
                            else:
                                print(f"   ⏳ Task not completed or failed")
                        else:
                            print(f"   ❌ API error: {response.status}")
                            
            except Exception as e:
                print(f"   ❌ Error checking task {task_id}: {e}")
    else:
        print(f"\n💡 0-6번 비디오를 찾으려면:")
        print(f"   1. 백엔드 로그에서 더 많은 task_id들을 찾아서 제공해주세요")
        print(f"   2. 또는 프론트엔드에서 새로운 프로젝트를 생성해서 전체 10개 비디오를 다시 만들어보세요")
        
        # 현재까지 다운로드된 비디오 확인
        await check_downloaded_videos()

async def check_downloaded_videos():
    """현재까지 다운로드된 비디오들을 확인"""
    videos_dir = "downloads/videos"
    
    print(f"\n📁 현재 다운로드된 비디오들:")
    
    if os.path.exists(videos_dir):
        video_files = [f for f in os.listdir(videos_dir) if f.endswith('.mp4')]
        
        if video_files:
            for video_file in sorted(video_files):
                file_path = os.path.join(videos_dir, video_file)
                file_size = os.path.getsize(file_path) / (1024*1024)  # MB
                print(f"   📹 {video_file} ({file_size:.2f} MB)")
        else:
            print(f"   ❌ 다운로드된 비디오가 없습니다")
    else:
        print(f"   ❌ videos 디렉토리가 없습니다")

async def manual_task_check():
    """수동으로 특정 task_id들을 확인하는 함수"""
    
    # 사용자가 제공할 수 있는 task_id들
    manual_task_ids = [
        # 여기에 로그에서 찾은 task_id들을 추가하세요
        # 예시: "274930302533001", "274930302533002", etc.
    ]
    
    print(f"\n🔧 수동 task_id 확인 (사용자가 추가로 제공한 경우):")
    
    if not manual_task_ids:
        print(f"   📝 manual_task_ids 리스트에 task_id들을 추가해주세요")
        return
    
    minimax_service = MinimaxService()
    
    for task_id in manual_task_ids:
        print(f"   🔍 Checking: {task_id}")
        # task_id 확인 로직...

if __name__ == "__main__":
    asyncio.run(find_and_download_missing_videos()) 