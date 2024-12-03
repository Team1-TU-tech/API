from fastapi import FastAPI, Request, HTTPException, Form
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from kakao_manager import KakaoAPI
import uvicorn
import logging

# 로깅 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 콘솔 핸들러 추가
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# 파일 핸들러 설정
file_handler = logging.FileHandler('./user_activity.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)



app = FastAPI()

# 세션 미들웨어를 앱에 추가, 'your-secret-key'는 실제 프로덕션에서는 안전한 값으로 변경해야 
app.add_middleware(SessionMiddleware, secret_key='your-secret-key')

# Jinja2 템플릿 엔진을 설정
templates = Jinja2Templates(directory="templates")

# KakaoAPI 인스턴스를 생성
kakao_api = KakaoAPI()




# 사용자 활동을 기록하는 엔드포인트
@app.post("/track-activity")
async def track_activity(request: Request):
    data = await request.json()
    user_id = request.session.get("user_id", "Anonymous")  # user_id를 세션에서 가져옴
    logger.info(f"User ID: {user_id}, Activity: {data.get('activity')}, Button ID: {data.get('button_id')}")
    return JSONResponse(content={"message": "Activity tracked successfully"})





# 카카오 로그인을 시작하기 위한 엔드포인트
@app.get("/getcode")
def get_kakao_code(request: Request):
    scope = 'profile_nickname, profile_image'  # 요청할 권한 범위
    kakao_auth_url = kakao_api.getcode_auth_url(scope)
    return RedirectResponse(kakao_auth_url)

# 카카오 로그인 후 카카오에서 리디렉션될 엔드포인트
# 카카오 로그인 후 사용자 정보를 세션에 저장
@app.get("/callback")
async def kakao_callback(request: Request, code: str):
    token_info = await kakao_api.get_token(code)
    logger.debug(f"Token info from Kakao: {token_info}")
    if "access_token" in token_info:
        access_token = token_info['access_token']
        request.session['access_token'] = access_token
        # 사용자 정보 가져오기
        user_info = await kakao_api.get_user_info(access_token)
        request.session['user_id'] = user_info['id']  # 사용자 ID를 세션에 저장
        logger.debug(f"Access token and user_id saved in session: {access_token}, {user_info['id']}")
        return RedirectResponse(url="/user_info", status_code=302)
    else:
        logger.error("Failed to authenticate with Kakao")
        return RedirectResponse(url="/?error=Failed to authenticate", status_code=302)


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
@app.get("/logout")
async def logout(request: Request):
    access_token = request.session.get('access_token')
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
    user_id = request.session.get('user_id')
    logger.debug(f"User ID in session: {user_id}")
    if user_id:
        user_info = await kakao_api.get_user_info(request.session['access_token'])
        logger.debug(f"User info retrieved: {user_info}")
        return templates.TemplateResponse("user_info.html", {"request": request, "user_info": user_info})
    else:
        logger.error("User ID not found in session")
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
    uvicorn.run(app, host="127.0.0.1", port=8000)
