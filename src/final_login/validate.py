from fastapi.security.utils import get_authorization_scheme_param
from fastapi import Request, HTTPException, status
from jose import jwt, JWTError
from typing import Optional, Dict
from dotenv import load_dotenv
import os
from src.final_login.db import user_collection, User
from fastapi import Depends, Request
from datetime import datetime 
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
            # 로그를 위한 timestamp, device, user_id 추출

        current_timestamp = datetime.now().isoformat()
        device = request.headers.get("User-Agent", "Unknown")
        user_id = str(user.id)
        # birthday = user.birthday
        # gender = user.gender

        try:
            # 로그 이벤트 기록
            log_event(
                current_timestamp=current_timestamp,
                user_id=user_id,  
                # birthday=birthday,
                # gender=gender,
                device=device,     
                action="Login"
            )
        except Exception as e:
            print(f"Error logging event: {e}")

        raise HTTPException(status_code=401, detail="Invalid credentials")
    return stored_user

