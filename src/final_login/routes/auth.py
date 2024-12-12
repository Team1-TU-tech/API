from fastapi import APIRouter
from datetime import timedelta
from src.final_login.db_model import User, TokenResponse
from src.final_login.token import SECRET_KEY, ALGORITHM
from fastapi import Depends, Request
from src.final_login.validate import validate_user
from src.final_login.token import create_access_token, create_refresh_token
from src.final_login.log_handler import log_event
from src.final_login.db_model import IDCheck

auth_router = APIRouter()

@auth_router.post("/login", response_model=TokenResponse)
async def login(request: Request, user: User = Depends(validate_user)):
    # 토큰 생성
    data = {"id": str(user["id"])}
    expires_delta = timedelta(minutes=30)
    refresh_token_expires_delta = timedelta(days=1)
    access_token = create_access_token(data, expires_delta, SECRET_KEY, ALGORITHM)
    refresh_token = create_refresh_token(data, refresh_token_expires_delta)
    
    # 로그를 위한 device, user_id, birthday, gender 추출
    device = request.headers.get("User-Agent", "Unknown")
    user_id = str(user["id"])
    birthday = user.get("birthday")
    gender = user.get("gender")

    try:
        # 로그 이벤트 기록
        log_event(
            user_id=user_id,  
            birthday=birthday,
            gender=gender,
            device=device,     
            action="Login"
        )
    except Exception as e:
        print(f"Error logging event: {e}")
                                                                                                                        
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer", 
    }


# 로그아웃할 때 프론트엔드에서 토큰 삭제를 명시적으로 처리해야 함
"""
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
"""
@auth_router.post("/logout")
async def logout(request: Request, user_id: IDCheck):

    # 로그를 위한 device, user_id 추출

    device = request.headers.get("User-Agent", "Unknown")

    try:
        # 로그 이벤트 기록
        log_event(
            user_id=user_id.id,  
            device=device,     
            action="Logout",   
        )
    except Exception as e:
        print(f"Error logging event: {e}")

    return {"message": "Logged out successfully"}

