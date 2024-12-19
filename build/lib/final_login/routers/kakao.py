from fastapi import APIRouter
from fastapi import Request, Header,  HTTPException
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
from src.final_login.kakao_manager import KakaoAPI
router = APIRouter()
kakao_api = KakaoAPI()
from src.final_login.log_handler import log_event
from datetime import datetime, timedelta

# 카카오 로그인을 시작하기 위한 엔드포인트
@router.get("/getcode")
def get_kakao_code(request: Request):
    scope = 'profile_nickname, profile_image, account_email'  # 요청할 권한 범위
    kakao_auth_url = kakao_api.getcode_auth_url(scope)
    return RedirectResponse(kakao_auth_url)

@router.get("/callback")
async def kakao_callback(request: Request, code: str):
    # 원하는 URL로 리다이렉트하면서 인가 코드 포함
    redirect_url = f"http://localhost:3000/callback?code={code}"
    return RedirectResponse(url=redirect_url)


# @router.get("/getToken")
# async def get_token(request: Request, code: str):
#     # code를 사용해서 토큰을 발급 받기
#     try:
#         token_info = await kakao_api.get_token(code)
#         if "access_token" in token_info:
#             access_token = token_info['access_token']
#             device = request.headers.get("User-Agent", "Unknown")
#             client_id = kakao_api.client_id

#             # 로그인 이벤트 기록
#             try:
#                 log_event(
#                     user_id=client_id,  # 또는 user_info에서 적절한 필드 사용
#                     device=device,
#                     action="Kakao Login",
#                     topic="KakaoLogin_log",
#                 )
#             except Exception as e:
#                 print(f"Failed to log login event: {str(e)}")

#             return JSONResponse(content={"access_token": access_token})
#         else:
#             return JSONResponse(content={"error": "Failed to get access token"}, status_code=400)
#     except Exception as e:
#         return JSONResponse(content={"error": str(e)}, status_code=400)


@router.get("/getToken")
async def get_token(request: Request, code: str):
    try:
        # 1. Kakao API를 사용하여 access_token 발급
        token_info = await kakao_api.get_token(code)
        if "access_token" not in token_info:
            return JSONResponse(content={"error": "Failed to get access token"}, status_code=400)
        
        access_token = token_info['access_token']

        # 2. Kakao API를 사용하여 사용자 정보 가져오기
        user_info = get_kakao_user_info(access_token)  # Kakao 사용자 정보 가져오기 함수
        client_id = user_info["id"]  # Kakao 사용자 ID
        nickname = user_info["properties"].get("nickname", "Unknown")

                # UTC 시간
        utc_now = datetime.utcnow()

        # 한국 시간(KST)으로 변환 (UTC + 9시간)
        kst_now = utc_now + timedelta(hours=9)

        # KST 시간 ISO 형식으로 출력
        create_at = kst_now.isoformat()
        # 3. DB에서 사용자 확인 및 저장
        user = await db.users.find_one({"client_id": client_id})  # client_id로 사용자 확인
        if not user:
            # 새로운 사용자 저장
            new_user = {
                "client_id": client_id,
                "nickname": nickname,
                "created_at": create_at
            }
            await db.users.insert_one(new_user)
            print(f"New user created: {new_user['client_id']}")
        else:
            print(f"User already exists: {user['client_id']}")

        # 4. 로그 기록
        device = request.headers.get("User-Agent", "Unknown")
        try:
            log_event(
                user_id=client_id,  # Kakao 사용자 ID
                device=device,
                action="Kakao Login",
                topic="KakaoLogin_log",
            )
        except Exception as e:
            print(f"Failed to log login event: {str(e)}")

        # 5. Access Token 반환
        return JSONResponse(content={"access_token": access_token})
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

            print("log_event 호출 데이터:", {
                "user_id": client_id,
                "device": device,
                "action": "Kakao Logout",
                "topic": "KakaoLogout_log",
            })



            # 로그 이벤트 기록
            log_event(
                user_id=client_id,
                device=device,
                action="Kakao Logout",
                topic="KakaoLogout_log",
            )
        except Exception as e:
            print(f"Failed to log logout event: {str(e)}")      
        
        
        return RedirectResponse(url=logout_url)  # 카카오 로그아웃 페이지로 리디렉션
    
    return RedirectResponse(url="/?error=Not logged in", status_code=302)