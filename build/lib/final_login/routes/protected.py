from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.final_login.utils import JWTManager
from src.final_login.utils import SECRET_KEY, ALGORITHM

protected_router = APIRouter()
auth_scheme = HTTPBearer()
jwt_manager = JWTManager()

@protected_router.get("/protected")
async def protected_route(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    try:
        payload = jwt_manager.decode(credentials.credentials, SECRET_KEY, ALGORITHM)
        return {"message": f"Welcome, {payload['sub']}!"}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
