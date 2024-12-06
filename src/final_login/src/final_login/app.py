from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
import os
from fastapi.security import OAuth2PasswordBearer  
from fastapi import BackgroundTasks
import time

# .env 파일 로드
load_dotenv()

# MongoDB URI 설정
mongopassword = os.getenv("MONGOPASS")
url = f"mongodb+srv://hahahello777:{mongopassword}@cluster0.5vlv3.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0"

# MongoDB 클라이언트 설정
client = AsyncIOMotorClient(url)
db = client.get_database("signup")
user_collection = db.get_collection("users")

# FastAPI 앱 설정
app = FastAPI()

# CORS 설정
origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.getenv("SECRET_KEY")  # .env에서 SECRET_KEY 로드
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # .env에서 ALGORITHM 로드, 기본값은 HS256
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))  # 기본값 15분
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))  # 기본값 7일

# 비밀번호 해싱을 위한 암호화 컨텍스트 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2PasswordBearer 정의 (토큰을 받기 위한 scheme)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Pydantic 모델 (로그인 요청 데이터)
class UserLogin(BaseModel):
    id: str
    pw: str

# Pydantic 모델 (리프레시 토큰 요청 데이터)
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: str

# JWT 토큰 생성 함수
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 리프레시 토큰 생성 함수
def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)  # 기본 7일 만료
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 비밀번호 확인 함수
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# 로그인 API
@app.post("/login")
async def login(user: UserLogin):
    # DB에서 사용자 정보 확인
    existing_user = await user_collection.find_one({"id": user.id})
    if not existing_user:
        raise HTTPException(status_code=400, detail="아이디 또는 비밀번호가 잘못되었습니다.")
    
    # 비밀번호 검증
    if not verify_password(user.pw, existing_user["password"]):
        raise HTTPException(status_code=400, detail="아이디 또는 비밀번호가 잘못되었습니다.")
    
    # JWT 액세스 토큰 생성
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.id}, expires_delta=access_token_expires)
    
    # 리프레시 토큰 생성
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(data={"sub": user.id}, expires_delta=refresh_token_expires)
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

# 리프레시 토큰을 사용하여 새로운 액세스 토큰 발급
@app.post("/refresh-token")
async def refresh_token(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=403, detail="리프레시 토큰이 유효하지 않습니다.")
        
        # 새로운 액세스 토큰 발급
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(data={"sub": username}, expires_delta=access_token_expires)
        
        return {"access_token": new_access_token, "token_type": "bearer"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다.")
    except jwt.JWTError:
        raise HTTPException(status_code=403, detail="유효하지 않은 토큰입니다.")

# 간단한 메모리 기반 블랙리스트 (배포 환경에서는 Redis 같은 외부 저장소 사용 권장)
token_blacklist = set()

# 로그아웃 API
@app.post("/logout")
async def logout(token: str = Depends(oauth2_scheme), background_tasks: BackgroundTasks = None):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=403, detail="유효하지 않은 토큰입니다.")
        
        # 토큰을 블랙리스트에 추가
        token_blacklist.add(token)

        # 만료된 토큰 제거를 위해 BackgroundTasks에 작업 추가
        def remove_token_from_blacklist(expire_time: datetime, token: str):
            delta = expire_time - datetime.utcnow()
            if delta.total_seconds() > 0:
                time.sleep(delta.total_seconds())
            token_blacklist.discard(token)
        
        expire_time = datetime.fromtimestamp(payload["exp"])
        background_tasks.add_task(remove_token_from_blacklist, expire_time, token)

        return {"message": "로그아웃이 완료되었습니다."}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다.")
    except jwt.JWTError:
        raise HTTPException(status_code=403, detail="유효하지 않은 토큰입니다.")

# 토큰 블랙리스트 확인
def check_token_blacklist(token: str):
    if token in token_blacklist:
        raise HTTPException(status_code=401, detail="이미 로그아웃된 토큰입니다.")
    
# JWT 토큰을 사용하여 사용자 정보 가져오기
def get_current_user(token: str = Depends(oauth2_scheme)):
    check_token_blacklist(token)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="토큰이 유효하지 않거나 만료되었습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except jwt.PyJWTError:
        raise credentials_exception
