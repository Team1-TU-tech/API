import httpx
import os
from dotenv import load_dotenv
import logging
from src.final_login.log_handler import log_event
from fastapi import Request


# 환경 변수 로드
load_dotenv()

class KakaoAPI:
    def __init__(self):
        # 카카오 API 관련 정보를 환경 변수에서 로드
        self.client_id = os.getenv('KAKAO_CLIENT_ID')
        self.client_secret = os.getenv('KAKAO_CLIENT_SECRET')
        self.redirect_uri = os.getenv('KAKAO_REDIRECT_URI')
        self.logout_redirect_uri = os.getenv('KAKAO_LOGOUT_REDIRECT_URI')
        self.headers={}
        
    def getcode_auth_url(self, scope):
        # 카카오 로그인을 위한 인증 URL 생성
        return f'https://kauth.kakao.com/oauth/authorize?response_type=code&client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope={scope}&prompt=login'
    

    async def get_token(self, code: str):
        token_request_url = 'https://kauth.kakao.com/oauth/token'
        token_request_payload = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code": code,
            "client_secret": self.client_secret
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_request_url, data=token_request_payload)
            response.raise_for_status()  # 상태 코드가 200이 아니면 예외 발생
            return response.json()


    async def logout(request: Request, client_id, logout_redirect_uri):
        
        if not logout_redirect_uri:
            raise ValueError("Logout redirect URI is missing.")
        else:
            print(f"Logout redirect URI: {logout_redirect_uri}")
            
        # 카카오 로그아웃 URL을 호출하여 로그아웃 처리
        logout_url = f"https://kauth.kakao.com/oauth/logout?client_id={client_id}&logout_redirect_uri={logout_redirect_uri}&state=state"
        print(f"Logout URI: {logout_url}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(logout_url)
                return logout_url
        
        except Exception as e:
            print(f"Error during logout process: {e}")
            return {"message": "Error occurred during logout", "logout_url": logout_url}