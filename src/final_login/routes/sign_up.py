from fastapi import APIRouter
from datetime import timedelta
from src.final_login.db_model import UserSignUp, UsernameCheck, user_collection
from fastapi import HTTPException
import uuid
from datetime import datetime, timedelta

signup_router = APIRouter()

@signup_router.post("/check-id")
async def check_username(username_check: UsernameCheck):
    # 아이디 중복 체크
    existing_user = await user_collection.find_one({"id": username_check.id})
    if existing_user:
        #return {"is_taken": True}  # 아이디가 이미 존재
        raise HTTPException(status_code=400, detail="아이디가 이미 존재합니다.")
    return {"is_taken": False}  # 아이디가 사용 가능

# 회원가입 API
@signup_router.post("/signup")
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
    return {"success": True}