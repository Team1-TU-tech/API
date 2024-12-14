from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from typing import Optional 
# 환경 변수 로드
load_dotenv()

MONGO_PASSWORD = os.getenv("MONGOPASS")
MONGO_URL = f"mongodb+srv://hahahello777:{MONGO_PASSWORD}@cluster0.5vlv3.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0"

# MongoDB 연결
client = AsyncIOMotorClient(MONGO_URL)
db = client.get_database("signup")
user_collection = db.get_collection("users")

# Pydantic 모델
# 유저 데이터터
class User(BaseModel):
    id: str
    password: str

# JWT 토큰 반환
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

# 회원가입 입력 데이터
class UserSignUp(BaseModel):
    username: str
    id: str
    pw: str
    email: str
    phoneNumber: str
    agreeMarketing: str
    gender: str
    birthday: str
    create_at: Optional[str] = None
    auth_id: Optional[str] = None

# 아이디 중복 체크
class IDCheck(BaseModel):
    id: str

# JWT 토큰 
class TokenBody(BaseModel):
    token: str