from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import timedelta
from .auth import create_access_token, create_refresh_token, SECRET_KEY, ALGORITHM
from .database import user_collection
from .log_handler import log_event

app = FastAPI()

class User(BaseModel):
    id: str
    password: str

@app.post("/login")
async def login(request: User):

    # MongoDB에서 사용자 정보 조회
    user = await user_collection.find_one({"id": request.id})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user["password"] != request.password:
        raise HTTPException(status_code=401, detail="Incorrect password")


    # JWT 토큰 생성
    expires_delta = timedelta(minutes=30)
    access_token = create_access_token({"id": user["id"]}, expires_delta, SECRET_KEY, ALGORITHM)

    # JWT 리프레시 토큰 생성
    refresh_token_expires_delta = timedelta(days=1)  #리프레시 토큰 유효 기간
    refresh_token = create_refresh_token({"id": user["id"]}, refresh_token_expires_delta)
    
    log_event(user_id=user["id"], birthday=user.get("birthday"))
    print(log_event)
    # 토큰 반환
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer", 
        "birthday": user.get("birthday"), 
        "gender": user.get("gender")
    }