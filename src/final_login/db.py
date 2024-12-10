from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.security.utils import get_authorization_scheme_param
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

MONGO_PASSWORD = os.getenv("MONGOPASS")
MONGO_URL = f"mongodb+srv://hahahello777:{MONGO_PASSWORD}@cluster0.5vlv3.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0"

# MongoDB 연결
client = AsyncIOMotorClient(MONGO_URL)
db = client.get_database("signup")
user_collection = db.get_collection("users")

# Pydantic 모델
class User(BaseModel):
    id: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str



