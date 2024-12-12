from fastapi import FastAPI, Request, HTTPException, Form
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from kakao_manager import KakaoAPI
import uvicorn
import logging
import httpx
from fastapi.middleware.cors import CORSMiddleware

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)




app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 세션 미들웨어를 앱에 추가, 'your-secret-key'는 실제 프로덕션에서는 안전한 값으로 변경해야 
app.add_middleware(SessionMiddleware, secret_key='your-secret-key')

# Jinja2 템플릿 엔진을 설정
templates = Jinja2Templates(directory="templates")

# KakaoAPI 인스턴스를 생성
kakao_api = KakaoAPI()

# 카카오 로그인을 시작하기 위한 엔드포인트
@app.get("/getcode")
def get_kakao_code(request: Request):
    scope = 'profile_nickname, profile_image'  # 요청할 권한 범위
    kakao_auth_url = kakao_api.getcode_auth_url(scope)
    return RedirectResponse(kakao_auth_url)

@app.get("/callback")
async def kakao_callback(request: Request, code: str):
    # 원하는 URL로 리다이렉트하면서 인가 코드 포함
    redirect_url = f"http://localhost:3000/callback?code={code}"
    logger.debug(f"Redirecting to: {redirect_url}")
    return RedirectResponse(url=redirect_url)

@app.get("/getToken")
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
    
# 엑세스 토큰으로부터 카카오에서 유저 정보 가져오려면 
#         user_info_response = await get_user_info_from_kakao(access_token)

# async def get_user_info_from_kakao(access_token: str):
#     url = "https://kapi.kakao.com/v2/user/me"
#     headers = {"Authorization": f"Bearer {access_token}"}

#     async with httpx.AsyncClient() as client:
#         response = await client.get(url, headers=headers)

#     if response.status_code == 200:
#         return response.json()  # 유저 정보 반환
#     else:
#         logger.error(f"Failed to fetch user info from Kakao: {response.text}")
#         return None

# 홈페이지 및 로그인/로그아웃 버튼을 표시
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    logged_in = 'access_token' in request.session
    return templates.TemplateResponse("index.html", {
        "request": request,
        "client_id": kakao_api.client_id,
        "redirect_uri": kakao_api.redirect_uri,
        "logged_in": logged_in
    })

# 로그아웃 처리 엔드포인트
#@app.get("/logout")
@app.post("/logout")
async def logout(request: Request, data:dict):
    #access_token = request.session.get('access_token')
    access_token = data
    logger.debug(f"Initial access_token in session: {access_token}")


    if access_token:
        # 카카오 로그아웃 처리
        client_id = kakao_api.client_id
        logout_redirect_uri = kakao_api.logout_redirect_uri
        logout_url = await kakao_api.logout(client_id, logout_redirect_uri)

        # 애플리케이션 내 세션에서 토큰 삭제
        request.session.pop('access_token', None)
        logger.debug("Access token removed from session")

        # 쿠키에서 access_token 삭제
        response = RedirectResponse(url="/")
        response.delete_cookie("access_token")  # 쿠키에서 access_token 삭제
        logger.debug("Access token removed from cookies")
        return RedirectResponse(url=logout_url)  # 카카오 로그아웃 페이지로 리디렉션
    
    logger.debug("No access_token in session")
    return RedirectResponse(url="/?error=Not logged in", status_code=302)

# 사용자 정보를 표시하기 위한 엔드포인트
@app.get("/user_info", response_class=HTMLResponse)
async def user_info(request: Request):
    access_token = request.session.get('access_token')
    logger.debug(f"Access token in session: {access_token}")
    if access_token:
        user_info = await kakao_api.get_user_info(access_token)
        logger.debug(f"User info retrieved: {user_info}") 
        return templates.TemplateResponse("user_info.html", {"request": request, "user_info": user_info})
    else:
        logger.error("Access token not found in session") 
        raise HTTPException(status_code=401, detail="Unauthorized")

# 액세스 토큰을 새로고침하기 위한 엔드포인트
@app.post("/refresh_token")
async def refresh_token(refresh_token: str = Form(...)):
    client_id = kakao_api.client_id
    logger.debug(f"Refreshing access token with refresh_token: {refresh_token}") 
    new_token_info = await kakao_api.refreshAccessToken(client_id, refresh_token)
    logger.debug(f"New token info after refresh: {new_token_info}")
    return new_token_info

# 애플리케이션을 실행하기 위한 코드
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3000)
