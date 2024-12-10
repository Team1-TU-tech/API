from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException, Depends, Request, status
from fastapi.security.utils import get_authorization_scheme_param
from pydantic import BaseModel
from abc import ABC, abstractmethod
from jose import JWTError, jwt
import jwt
from datetime import datetime, timedelta
from typing import Any, Dict
import os
from dotenv import load_dotenv
from fastapi import FastAPI

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

# Pydantic 모델
class User(BaseModel):
    id: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str

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

class JWTService:
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7

    def create_access_token(self, data: Dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, self.algorithm)

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, self.algorithm)

    def check_token_expired(self, token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

jwt_service = JWTService()

# 토큰 유효성 검사
async def validate_token(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    scheme, param = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return param

# JWT 인증 클래스
class JWTAuthentication:
    async def __call__(self, token: str = Depends(validate_token)) -> User:
        try:
            valid_payload = jwt_service.check_token_expired(token)
            if valid_payload:
                user_id = valid_payload.get("id")
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Expired or invalid token.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 데이터베이스에서 사용자 검색
        user = await user_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return User(**user) # Pydantic 모델을 통한 데이터의 유효성 검증, User 모델에서 id와 password가 필수 항목으로 지정되어 있다면, 데이터가 누락되었을 때 오류를 발생
        #return user

get_current_user = JWTAuthentication()


# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI()


# 로그인 엔드포인트
@app.post("/login")
def login(request: User):
    # 사용자 인증 (비밀번호 확인)
    #user = await user_collection.find_one({"id": request.id})

    #if user and user["password"] == request.password:  # 비밀번호 확인
        # JWT 토큰 생성
    #jwt_manager = JWTManager()
    expires_delta = timedelta(minutes=30)  # 토큰 만료 시간 설정
    token = jwt_manager.encode({"id": request.id}, expires_delta, SECRET_KEY, ALGORITHM)
    
    # 디버깅: 생성된 JWT 디코딩하여 payload 확인
    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    print("Decoded JWT Payload:", decoded_token)

    # 토큰 반환
    return {"access_token": token, "token_type": "bearer"}

    #raise HTTPException(status_code=401, detail="Invalid credentials")