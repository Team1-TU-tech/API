from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.final_login.routes.auth import auth_router
from src.final_login.routes.sign_up import signup_router

app = FastAPI()

# CORS 설정
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth_router, prefix="/auth")
app.include_router(signup_router, prefix="/signup")