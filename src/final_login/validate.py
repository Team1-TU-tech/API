from fastapi import Request, HTTPException
from jose import jwt, JWTError
from typing import Dict
from dotenv import load_dotenv
import os
from src.final_login.db_model import user_collection, User
from fastapi import Request
from src.final_login.log_handler import log_event
from datetime import datetime, timedelta
from src.final_login.routers.kakao import *

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

def create_access_token(data: Dict[str, str], expires_delta: timedelta, SECRET_KEY, algorithm=ALGORITHM) -> str:
    """ Access Token 생성 """
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: Dict[str, str], expires_delta: timedelta) -> str:
    """ Refresh Token 생성 """
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# access token 재발급 함수
def refresh_access_token(refresh_token: str, SECRET_KEY: str, ALGORITHM: str, expires_delta: timedelta):
    try:
        # refresh token 검증
        decoded_refresh_token = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_data = decoded_refresh_token  

        # 새로운 access token 발급
        new_access_token = create_access_token(user_data, expires_delta, SECRET_KEY, ALGORITHM)
        return new_access_token
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
# 로그인이 성공적으로 이루어진 후, 사용자가 API 요청을 보낼 때마다 보낸 access token을 검증할 때 이용함
def verify_token(token: str, SECRET_KEY: str, ALGORITHM: str, refresh_token: str, expires_delta: timedelta) -> Dict[str, str]:
    """ JWT 토큰 검증 및 만료된 경우 refresh token으로 access token 재발급 """
    try:
        # Access token 검증
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # 토큰이 만료되었는지 확인 (만료되었다면 refresh token 사용)
        if datetime.utcfromtimestamp(decoded_token['exp']) < datetime.utcnow():
            # 만약 만료되었다면 refresh token을 사용하여 새로운 access token 발급
            new_access_token = refresh_access_token(refresh_token, SECRET_KEY, ALGORITHM, expires_delta)
            return {"access_token": new_access_token}
        
        return decoded_token

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
async def validate_user(request: Request, user: User):
    stored_user = await user_collection.find_one({"id": user.id})
    if not stored_user or stored_user["password"] != user.password:

        device = request.headers.get("User-Agent", "Unknown")
        user_id = "anonymous"

        try:
            # 로그 이벤트 기록
            log_event(
                user_id=user_id,  
                device=device,     
                action="User Validate failed",
                topic="Validate",
                error="Invalid credentials or user not found" 
            )
            raise HTTPException(status_code=401, detail="Invalid credentials")
        except HTTPException as e:
            raise e  # HTTPException을 다시 raise하여 클라이언트에게 전달
    return stored_user


async def token_decode_verify(request: Request):

    user_id = request.headers.get("id", "anonymous")
    token = request.headers.get("Authorization")

    gender = None  # 기본값
    birthday = None  # 기본값
    email = None # 기본값


    if not token:
        return {"user_id": user_id, "gender": gender, "birthday": birthday, "email": email}

    try:
        # JWT 형식인지 확인
        if "." in token and len(token.split(".")) == 3:
            # JWT 디코딩 로직
            try:
                decoded_token = verify_token(
                    token=token,
                    SECRET_KEY=SECRET_KEY,
                    ALGORITHM=ALGORITHM,
                    refresh_token=None,
                    expires_delta=None
                )
                user_id = decoded_token.get("id", "anonymous")
                user_info = await user_collection.find_one({"id": user_id})
                if user_info:
                    gender = user_info.get("gender", None)
                    birthday = user_info.get("birthday", None)
                    email = user_info.get("email", None)
            except JWTError as e:
                raise HTTPException(status_code=401, detail="Invalid JWT token.")
        else:
            # Step 1: Kakao API를 사용하여 사용자 정보 가져오기
            user_info = kakao_api.get_kakao_user_info(token)  # `token`이 access_token으로 전달됨
            #print("[DEBUG] User info fetched from Kakao API:", user_info)
            
            user_id = user_info["id"]
            email = user_info.get("kakao_account", {}).get("email", None)
            # Step 2: MongoDB에서 user_id 조회
            user = await kakao_collection.find_one({"user_id": user_id})  # MongoDB에서 user_id 조회
            
            if user:
                gender = user.get("gender", None)
                birthday = user.get("birthday", None)
                email = user.get("email", None)
            else:
                raise HTTPException(status_code=401, detail="User not found in Kakao collection")
            
    except HTTPException as e:
        raise HTTPException(status_code=401, detail="Token verification failed.")

    return {"user_id": user_id, "gender": gender, "birthday": birthday, "email": email}