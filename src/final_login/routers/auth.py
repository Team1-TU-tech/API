from fastapi import APIRouter, HTTPException
from datetime import timedelta
from src.final_login.db_model import User, TokenResponse
from src.final_login.token import SECRET_KEY, ALGORITHM
from fastapi import Depends, Request
from src.final_login.validate import validate_user, verify_token
from src.final_login.token import create_access_token, create_refresh_token
from src.final_login.log_handler import log_event
from jose import JWTError, ExpiredSignatureError

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(request: Request, user: User = Depends(validate_user)):

    # user는 validate_user에서 반환된 stored_user 데이터
    user_id = user["id"]
    username = user.get("username", "Unknown")
    user_type = user.get("user_type", 0)

    # 토큰 생성
    data = {"id": str(user["id"])}
    expires_delta = timedelta(minutes=30)
    refresh_token_expires_delta = timedelta(days=1)
    access_token = create_access_token(data, expires_delta, SECRET_KEY, ALGORITHM)
    refresh_token = create_refresh_token(data, refresh_token_expires_delta)
    
    # 로그를 위한 device, user_id, birthday, gender 추출
    device = request.headers.get("User-Agent", "Unknown")
    ip_address = request.client.host  # 클라이언트의 IP 주소
    user_id = str(user["id"])
    birthday = user.get("birthday")
    gender = user.get("gender")
    create_at = user.get("create_at")

    try:
        # 로그 이벤트 기록
        log_event(
            user_id=user_id,  
            birthday=birthday if birthday not in [None, ""] else "None",
            gender=gender if gender not in [None, ""] else "None",
            device=device,     
            action="Login",
            topic="Login_log",
            ip_address= ip_address,
            create_at=create_at
        )
    except Exception as e:
        print(f"Error logging event: {e}")
                                                                                                                        
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer", 
        "username": username,
        "user_type": user_type
    }


# 로그아웃할 때 프론트엔드에서 토큰 삭제를 명시적으로 처리해야 함
"""
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
"""

@router.post("/logout")
async def logout(request: Request):
    # 요청 본문에서 JWT 토큰 확인
    token = request.headers.get("Authorization")

    if not token:
        print("Token is missing in the Authorization header.")
        raise HTTPException(status_code=400, detail="Token is missing in the Authorization header.")

    # 토큰 검증 및 디코딩
    try:
        decoded_token = verify_token(
            token=token,
            SECRET_KEY=SECRET_KEY,
            ALGORITHM=ALGORITHM,
            refresh_token=None,
            expires_delta=None
        )
    except ExpiredSignatureError:
        # 토큰이 만료되었을 경우, 로그아웃을 허용
        print("Token is expired. Proceeding with logout.")
        decoded_token = None  # 만료된 토큰이라도 로그아웃 진행
    except JWTError as e:
        print(f"Token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token.")

    # 디코드된 데이터에서 사용자 ID 추출
    user_id = decoded_token.get("id", "anonymous")
    device = request.headers.get("User-Agent", "Unknown")
    ip_address = request.client.host

    #print(f"Decoded user_id: {user_id}")  # 디버깅 출력

    # 로그 기록
    try:
        log_event(
            user_id=user_id,  
            device=device,     
            action="Logout",   
            topic="Logout_log",
            ip_address= ip_address
        )
    except Exception as e:
        print(f"Error logging event: {e}")

    return {"message": "Logged out successfully"}