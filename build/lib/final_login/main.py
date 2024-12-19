from fastapi import FastAPI
from src.final_login.routers import tickets, banner, weekend, rank, auth, kakao, sign_up, ml, exclusive_main, exclusive_all  # tickets 라우터를 포함한 모듈
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv



app = FastAPI()

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


# CORS 설정
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터를 메인 앱에 연결
app.include_router(tickets.router)
app.include_router(banner.router)
app.include_router(rank.router)
app.include_router(weekend.router)

app.include_router(auth.router, prefix="/auth")
app.include_router(sign_up.router, prefix="/signup")
app.include_router(kakao.router, prefix="/kakao")

app.include_router(ml.router)
app.include_router(exclusive_main.router)
app.include_router(exclusive_all.router)