from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from abc import ABC, abstractmethod
from jose import JWTError, jwt

import jwt
from datetime import datetime, timedelta
from typing import Any, Dict
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 환경 설정
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

MONGO_PASSWORD = os.getenv("MONGOPASS")
MONGO_URL = f"mongodb+srv://hahahello777:{MONGO_PASSWORD}@cluster0.5vlv3.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0"

# MongoDB 연결
client = AsyncIOMotorClient(MONGO_URL)
db = client.get_database("signup")
user_collection = db.get_collection("users")

# JWT 추상 클래스
class JWTEncoder(ABC):
    @abstractmethod
    def encode(self, data: Dict[str, Any], expires_delta: timedelta, secret_key: str, algorithm: str) -> str:
        pass

class JWTDecoder(ABC):
    @abstractmethod
    def decode(self, token: str, secret_key: str, algorithm: str) -> Dict[str, Any]:
        pass

# JWT 관리 클래스
class JWTManager(JWTEncoder, JWTDecoder):
    def encode(self, data: Dict[str, Any], expires_delta: timedelta, secret_key: str, algorithm: str) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, secret_key, algorithm)

    def decode(self, token: str, secret_key: str, algorithm: str) -> Dict[str, Any]:
        try:
            return jwt.decode(token, secret_key, algorithms=[algorithm])
        except JWTError:
            return None
# JWT 매니저 인스턴스
jwt_manager = JWTManager()

# Pydantic 모델
class User(BaseModel):
    id: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
