from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import uuid
from datetime import datetime
from typing import Optional 

app = FastAPI()

# MongoDB 연결 설정 (로컬 또는 클라우드 MongoDB 사용)
client = MongoClient("mongodb+srv://hahahello777:VIiYTK9NobgeM1hk@cluster0.5vlv3.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0")

db = client["signup"]
users_collection = db["users"]

# Pydantic 모델: 회원가입 데이터
class UserSignup(BaseModel):
    user_id: str
    password: str
    username: str
    email: str
    gender: str
    birthday: str
    phone_number: str
    create_at: Optional[str] = None
    auth_id: Optional[str] = None

    class Config:
        min_anystr_length = 1 # 문자열의 최소 길이를 1로 설정
        anystr_strip_whitespace = True # 자동으로 앞뒤 공백을 제거

# UUID 생성 함수
def generate_auth_id():
    return str(uuid.uuid4())

# 아이디 중복 체크 (한글자씩 입력할 때마다 호출)
@app.get("/check_user_id/{user_id}")
async def check_user_id(user_id: str):
    # 아이디 길이가 1자 이상일 경우만 검사
    if len(user_id) >= 1:
        if users_collection.find_one({"user_id": user_id}):
            return {"available": False}
        return {"available": True}
    # 1자 이하의 아이디는 중복 체크할 필요 없으므로 True 반환
    return {"available": True}

# 회원가입 처리
@app.post("/signup")
async def signup(user: UserSignup):
        # 중복된 아이디는 회원가입 시 확인
    if users_collection.find_one({"user_id": user.user_id}):
        raise HTTPException(status_code=400, detail="아이디가 이미 존재합니다.")
    
    # auth_id 생성
    auth_id = generate_auth_id()

    # 회원가입 시간 생성
    create_at = datetime.utcnow().isoformat()

    # 사용자 정보 저장
    new_user = {
        "user_id": user.user_id,
        "password": user.password,
        "username": user.username,
        "email": user.email,
        "gender": user.gender,
            "birthday": user.birthday,
            "phone_number": user.phone_number,
        "create_at": create_at,
        "auth_id": auth_id
    }

    # MongoDB에 사용자 정보 삽입
    users_collection.insert_one(new_user)

    return {"message": "회원가입 성공"}
