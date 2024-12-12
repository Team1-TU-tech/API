from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
from src.final_login.kakao_manager import KakaoAPI

kakao_router = APIRouter()

kakao_api = KakaoAPI()

# 카카오 로그인을 시작하기 위한 엔드포인트
@kakao_router.get("/getcode")
def get_kakao_code(request: Request):
    scope = 'profile_nickname, profile_image, account_email'  # 요청할 권한 범위
    kakao_auth_url = kakao_api.getcode_auth_url(scope)
    return RedirectResponse(kakao_auth_url)

@kakao_router.get("/callback")
async def kakao_callback(request: Request, code: str):
    # 원하는 URL로 리다이렉트하면서 인가 코드 포함
    redirect_url = f"http://localhost:3000/callback?code={code}"
    return RedirectResponse(url=redirect_url)


@kakao_router.get("/getToken")
async def get_token(request: Request, code: str):
    # code를 사용해서 토큰을 발급 받기
    try:
        token_info = await kakao_api.get_token(code)
        if "access_token" in token_info:
            access_token = token_info['access_token']
            return JSONResponse(content={"access_token": access_token})
        else:
            return JSONResponse(content={"error": "Failed to get access token"}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)
    

# 로그아웃 처리 엔드포인트
@kakao_router.post("/logout")
async def logout(request: Request, data:dict):
    access_token = data

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
        return RedirectResponse(url=logout_url)  # 카카오 로그아웃 페이지로 리디렉션
    
    return RedirectResponse(url="/?error=Not logged in", status_code=302)