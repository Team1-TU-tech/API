from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
from jose import JWTError
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import bcrypt

# .env 파일 로드
load_dotenv()

# MongoDB URI 설정
mongopassword = os.getenv("MONGOPASS")
url = f"mongodb+srv://hahahello777:{mongopassword}@cluster0.5vlv3.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0"

# FastAPI 앱 생성
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

# MongoDB 클라이언트 설정
client = AsyncIOMotorClient(url)
db = client.get_database("signup")
user_collection = db.get_collection("users")
