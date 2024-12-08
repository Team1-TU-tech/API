from fastapi import APIRouter, HTTPException
from datetime import timedelta
from src.final_login.utils import JWTManager, JWTService
from src.final_login.utils import user_collection, User, TokenResponse
from src.final_login.utils import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi import HTTPException, Depends, Request, status
auth_router = APIRouter()
jwt_manager = JWTManager()
jwt_service = JWTService()

async def validate_user(user: User):
    stored_user = await user_collection.find_one({"id": user.id})
    if not stored_user or stored_user["password"] != user.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return stored_user

# 로그인, 토큰 생성
@auth_router.post("/login", response_model=TokenResponse)
async def login(user: User = Depends(validate_user)):
    data = {"id": str(user["id"])}
    access_token = jwt_service.create_access_token(data)
    refresh_token = jwt_service.create_refresh_token(data)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }

# 로그아웃할 때 프론트엔드에서 토큰 삭제를 명시적으로 처리해야 함
"""
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
"""
@auth_router.post("/logout")
async def logout():
    return {"message": "Logged out successfully"}

