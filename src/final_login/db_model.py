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
kakao_collection = db.get_collection("kakao")

# Pydantic 모델
class User(BaseModel):
    id: str
    password: str

class TicketData(BaseModel):
    id: str
    poster_url: Optional[str]
    title: Optional[str]
    location: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    category: Optional[str]
    isExclusive: bool
    onSale: bool
    like: bool
    
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    username: str
    user_type: str

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
    user_type: Optional[int] = 0  
    
class IDCheck(BaseModel):
    id: str

class LikePerfId(BaseModel):
    id: str
