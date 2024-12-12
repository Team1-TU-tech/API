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
    
    async def get_token(request: Request, self, code: str, device: str):
        # 카카오로부터 인증 코드를 사용해 액세스 토큰 요청
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
        result = response.json()

        # 액세스 토큰 받기
        access_token = result.get('access_token')

        if not access_token:
            raise Exception("Failed to retrieve access token")

        # 액세스 토큰을 사용하여 카카오 사용자 정보 요청
        user_info_url = 'https://kapi.kakao.com/v2/user/me'
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        async with httpx.AsyncClient() as client:
            user_info_response = await client.get(user_info_url, headers=headers)
        
        # 사용자 정보 받아오기
        user_info = user_info_response.json()
        ####디버깅####
        print(user_info)

        account_email = user_info.get("kakao_account", {}).get("email")
        device = request.headers.get("User-Agent", "Unknown")

        # 로그 기록: 인증 토큰 요청 시작
        log_event(
            user_id=self.client_id,
            device=device,
            action="KakaoLogin",
            account_email=account_email
        )
        return result
    

    async def logout(request: Request, client_id, logout_redirect_uri):
        
        if not logout_redirect_uri:
            raise ValueError("Logout redirect URI is missing.")
        else:
            print(f"Logout redirect URI: {logout_redirect_uri}")
            
        # 카카오 로그아웃 URL을 호출하여 로그아웃 처리
        logout_url = f"https://kauth.kakao.com/oauth/logout?client_id={client_id}&logout_redirect_uri={logout_redirect_uri}&state=state"
        print(f"Logout URI: {logout_url}")
        
        device = request.headers.get("User-Agent", "Unknown")
        try:
            log_event(
                user_id=client_id,  
                action="Logout",  
                device=device,    
            )
            
            async with httpx.AsyncClient() as client:
                response = await client.get(logout_url)
                return logout_url
            
        except Exception as e:
            print(f"Error during logout process: {e}")
            return {"message": "Error occurred during logout", "logout_url": logout_url}