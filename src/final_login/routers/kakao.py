from fastapi import APIRouter, Request, Header,  HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from src.final_login.log_handler import log_event
from datetime import datetime, timedelta
from src.final_login.db_model import kakao_collection
from dotenv import load_dotenv
import os
import httpx
import requests

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

        #print(f"[DEBUG] Request payload: {token_request_payload}")

        async with httpx.AsyncClient() as client:
            response = await client.post(token_request_url, data=token_request_payload)
            #print(f"[DEBUG] Response text: {response.text}")
            response.raise_for_status()  # 상태 코드가 200이 아니면 예외 발생
            return response.json()


    async def logout(request: Request, client_id, logout_redirect_uri):
        
        if not logout_redirect_uri:
            raise ValueError("Logout redirect URI is missing.")
        else:
            print(f"Logout redirect URI: {logout_redirect_uri}")
            
        # 카카오 로그아웃 URL을 호출하여 로그아웃 처리
        logout_url = f"https://kauth.kakao.com/oauth/logout?client_id={client_id}&logout_redirect_uri={logout_redirect_uri}&state=state"
        #print(f"Logout URI: {logout_url}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(logout_url)
                return logout_url
        
        except Exception as e:
            print(f"Error during logout process: {e}")
            return {"message": "Error occurred during logout", "logout_url": logout_url}
        

    def get_kakao_user_info(self, access_token: str):
        url = "https://kapi.kakao.com/v2/user/me"
        self.headers = {"Authorization": f"Bearer {access_token}"}
        print("[DEBUG] Request headers for user info:", self.headers)

        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()  # 사용자 정보 반환
        else:
            raise HTTPException(status_code=401, detail="Invalid Kakao access token")
        

router = APIRouter()
kakao_api = KakaoAPI()
API_APP_HOST = os.getenv("API_APP_HOST", "localhost")


# 카카오 로그인을 시작하기 위한 엔드포인트
@router.get("/getcode")
def get_kakao_code(request: Request):
    scope = 'profile_nickname, profile_image, account_email'  # 요청할 권한 범위
    kakao_auth_url = kakao_api.getcode_auth_url(scope)
    return RedirectResponse(kakao_auth_url)

@router.get("/callback")
async def kakao_callback(request: Request, code: str):
    # 원하는 URL로 리다이렉트하면서 인가 코드 포함
    redirect_url = f"http://{API_APP_HOST}/callback?code={code}"
    #redirect_url = f"http://www.ticket-moa.net/callback?code={code}"
    return RedirectResponse(url=redirect_url)

@router.get("/getToken")
async def get_token(request: Request, code: str):
    try:
        # Step 1: Kakao API를 사용하여 access_token 발급
        token_info = await kakao_api.get_token(code)

        if "access_token" not in token_info:
            return JSONResponse(content={"error": "Failed to get access token"}, status_code=400)
        
        access_token = token_info['access_token']

        # Step 2: Kakao API를 사용하여 사용자 정보 가져오기
        user_info = kakao_api.get_kakao_user_info(access_token)
        #print(f"[DEBUG] User info response: {user_info}")

        user_id = user_info["id"]  # Kakao 사용자 ID
        nickname = user_info["properties"].get("nickname", "Unknown")
        email = user_info.get("kakao_account", {}).get("email", "Unknown")

        # UTC 시간
        utc_now = datetime.utcnow()

        # 한국 시간(KST)으로 변환 (UTC + 9시간)
        kst_now = utc_now + timedelta(hours=9)

        # KST 시간 ISO 형식으로 출력
        create_at = kst_now.isoformat()

        # Step 3: DB에서 사용자 확인 및 저장
        user = await kakao_collection.find_one({"user_id": user_id})

        if not user:
            # 새로운 사용자 저장
            new_user = {
                "user_id": user_id,
                "nickname": nickname,
                "email": email,
                "created_at": create_at,
                "user_type" : 0 # 일반 사용자는 0, 관리자는 1
            }
            await kakao_collection.insert_one(new_user)
            user_type : 0  # 카카오 가입한 유저는 모두 일반 사용자

        else:
            print(f"[DEBUG] User already exists in DB: {user}")
            user_type = user.get("user_type", 0)

        # Step 4: 로그 기록
        device = request.headers.get("User-Agent", "Unknown")

        try:
            log_event(
                user_id=user_id,
                email=email,
                device=device,
                action="Kakao Login",
                topic="KakaoLogin_log",
            )
        except Exception as e:
            print(f"Failed to log login event: {str(e)}")

        # Step 5: Access Token, 유저 아이디, 관리자 여부 반환
        return JSONResponse(content={
            "access_token": access_token,
            "nickname": nickname,
            "user_type": user_type
        })
    
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)



# 로그아웃 처리 엔드포인트
@router.post("/logout")
async def logout(request: Request, authorization: str = Header(None)):
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header is missing")

    # 토큰 값 그대로 사용 
    access_token = authorization

    if access_token:
        # 카카오 로그아웃 처리
        user_info = kakao_api.get_kakao_user_info(access_token)
        user_id = user_info["id"]  # Kakao 사용자 ID
        email = user_info.get("kakao_account", {}).get("email", "Unknown")

        client_id = kakao_api.client_id
        logout_redirect_uri = kakao_api.logout_redirect_uri
        logout_url = await kakao_api.logout(client_id, logout_redirect_uri)
      
        # 애플리케이션 내 세션에서 토큰 삭제
        request.session.pop('access_token', None)

        # 쿠키에서 access_token 삭제
        response = RedirectResponse(url="/")
        response.delete_cookie("access_token")  # 쿠키에서 access_token 삭제

        # 로그를 위한 device 추출
        device = request.headers.get("User-Agent", "Unknown")
        
        try:

            # 로그 이벤트 기록
            log_event(
                user_id=user_id,
                email=email,
                device=device,
                action="Kakao Logout",
                topic="KakaoLogout_log",
            )
        except Exception as e:
            print(f"Failed to log logout event: {str(e)}")      
        
        return RedirectResponse(url=logout_url)  # 카카오 로그아웃 페이지로 리디렉션
    
    return RedirectResponse(url="/?error=Not logged in", status_code=302)
