from fastapi import APIRouter, HTTPException
from datetime import timedelta
from src.final_login.utils import JWTManager
from src.final_login.utils import User, TokenResponse
from src.final_login.utils import user_collection
from src.final_login.utils import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

auth_router = APIRouter()
jwt_manager = JWTManager()

@auth_router.post("/login", response_model=TokenResponse)
async def login(user: User):
    stored_user = await user_collection.find_one({"id": user.id})
    if not stored_user or stored_user["password"] != user.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = jwt_manager.encode(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        secret_key=SECRET_KEY,
        algorithm=ALGORITHM
    )
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.post("/logout")
async def logout():
    return {"message": "Logged out successfully"}
