from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.final_login.utils import JWTManager
from src.final_login.utils import SECRET_KEY, ALGORITHM

protected_router = APIRouter()
auth_scheme = HTTPBearer()
jwt_manager = JWTManager()

# 로그인 후 인증된 사용자만 접근할 수 있도록 보호된 엔드포인트 정의 (ex, 관리자 페이지)
@protected_router.get("/protected")
async def protected_route(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    try:
        payload = jwt_manager.decode(credentials.credentials, SECRET_KEY, ALGORITHM)
        return {"message": f"Welcome, {payload['sub']}!"}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
