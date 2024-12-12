from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import Optional 
import uvicorn
import os
import uuid
from datetime import datetime, timedelta

# .env 파일 로드
load_dotenv()

# MongoDB URI 설정
mongopassword = os.getenv("MONGOPASS")
url = f"mongodb+srv://hahahello777:{mongopassword}@cluster0.5vlv3.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0"

# MongoDB 클라이언트 설정
client = AsyncIOMotorClient(url)
db = client.get_database("signup") 
user_collection = db.get_collection("users") 
db = client['signup']
user_collection = db['users']

# FastAPI 앱 설정
app = FastAPI()

# CORS 설정
origins = [
    "http://localhost:3000",  # React 앱이 실행되는 주소
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# Pydantic 모델 (회원가입 요청 데이터)
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

# Pydantic 모델 (아이디 중복 체크 요청 데이터)
class UsernameCheck(BaseModel):
    id: str

# 아이디 중복 체크 API
@app.post("/check-id")
async def check_username(username_check: UsernameCheck):
    # 아이디 중복 체크
    existing_user = await user_collection.find_one({"id": username_check.id})
    if existing_user:
        #return {"is_taken": True}  # 아이디가 이미 존재
        raise HTTPException(status_code=400, detail="아이디가 이미 존재합니다.")
    return {"is_taken": False}  # 아이디가 사용 가능

# 회원가입 API
@app.post("/signup")
async def signup(user: UserSignUp):

    # 저장 전 아이디 중복 체크 (백엔드에서 최종확인)
    existing_user = await user_collection.find_one({"id": user.id})
    if existing_user:
        raise HTTPException(status_code=400, detail="아이디가 이미 존재합니다.")  # 아이디가 이미 존재하는 경우 오류 발생
    
    auth_id = str(uuid.uuid4())

    # UTC 시간
    utc_now = datetime.utcnow()

    # 한국 시간(KST)으로 변환 (UTC + 9시간)
    kst_now = utc_now + timedelta(hours=9)

    # KST 시간 ISO 형식으로 출력
    create_at = kst_now.isoformat()

    # 새 사용자 추가
    user_data = {
        "username": user.username,
        "id": user.id, 
        "password": user.pw,  
        "email": user.email, 
        "phoneNumber": user.phoneNumber, 
        "agreeMarketing": user.agreeMarketing, 
        "gender": user.gender,  
        "birthday": user.birthday, 
        "create_at": create_at,  
        "auth_id": auth_id
    }

    # 사용자 정보 DB에 저장
    result = await user_collection.insert_one(user_data)

    #return {"message": "회원가입이 완료되었습니다.", "user_id": str(result.inserted_id)}
    return {"success": True}

# 서버 실행
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
