from fastapi import Request, HTTPException
from jose import jwt
from typing import Dict
from dotenv import load_dotenv
import os
from src.final_login.db_model import user_collection, User
from fastapi import Request
from src.final_login.log_handler import log_event

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_token(token: str) -> Dict[str, str]:
    """ JWT 토큰 검증 """
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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
                error="Invalid credentials or user not found" 
            )
            raise HTTPException(status_code=401, detail="Invalid credentials")
        except HTTPException as e:
            raise e  # HTTPException을 다시 raise하여 클라이언트에게 전달
    return stored_user

