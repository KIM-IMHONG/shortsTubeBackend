from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import asyncio
import os
import time
from typing import List
import requests
import uuid

class KreaAutomation:
    def __init__(self):
        self.driver = None
        self.download_dir = "downloads/krea_images"
        os.makedirs(self.download_dir, exist_ok=True)
        
    async def setup(self):
        """Chrome WebDriver 설정"""
        options = webdriver.ChromeOptions()
        # 개발 중에는 헤드리스 모드 비활성화
        # options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # 다운로드 설정
        prefs = {
            "download.default_directory": os.path.abspath(self.download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
    async def login(self):
        """Krea 로그인"""
        email = os.getenv("KREA_EMAIL")
        password = os.getenv("KREA_PASSWORD")
        
        if not email or not password:
            raise ValueError("KREA_EMAIL and KREA_PASSWORD must be set in .env")
            
        self.driver.get("https://www.krea.ai/login")
        await asyncio.sleep(2)
        
        try:
            # 이메일 입력
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            email_field.send_keys(email)
            
            # 비밀번호 입력
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.send_keys(password)
            
            # 로그인 버튼 클릭
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            await asyncio.sleep(3)
            
        except Exception as e:
            print(f"Login error: {e}")
            raise
            
    async def generate_images(self, prompts: List[str]) -> List[List[str]]:
        """프롬프트 리스트를 받아 이미지 생성"""
        all_images = []
        
        for i, prompt in enumerate(prompts):
            print(f"Generating images for prompt {i+1}/10: {prompt[:50]}...")
            images = await self._generate_single_prompt(prompt, i)
            all_images.append(images)
            await asyncio.sleep(2)
            
        return all_images
        
    async def _generate_single_prompt(self, prompt: str, index: int) -> List[str]:
        """단일 프롬프트로 이미지 생성 (실제 구현은 Krea 웹사이트에 맞게 수정 필요)"""
        # MVP를 위한 더미 이미지 생성
        # 실제로는 Krea 웹사이트 자동화
        dummy_images = []
        
        for j in range(4):
            # 임시로 placeholder 이미지 사용
            image_path = f"{self.download_dir}/prompt_{index}_image_{j}.jpg"
            
            # Placeholder 이미지 다운로드
            response = requests.get(f"https://picsum.photos/512/512?random={index}_{j}")
            with open(image_path, 'wb') as f:
                f.write(response.content)
                
            dummy_images.append(image_path)
            
        return dummy_images
        
    async def cleanup(self):
        """브라우저 종료"""
        if self.driver:
            self.driver.quit() 