from fastapi import APIRouter
from datetime import timedelta
from src.final_login.db_model import UserSignUp, IDCheck, user_collection
from fastapi import HTTPException
import uuid
from datetime import datetime, timedelta
from src.final_login.log_handler import log_event
from fastapi import Request
from pymongo.errors import PyMongoError

router = APIRouter()

@router.post("/check-id")
async def check_username(request: Request, username_check: IDCheck):

    user_id = "anonymous"  # 아직 로그인 전이므로 anonymous로 설정
    device = request.headers.get("User-Agent", "Unknown Device")
    ip_address = request.client.host  # 클라이언트의 IP 주소

    # 아이디 중복 체크
    existing_user = await user_collection.find_one({"id": username_check.id}) 
    if existing_user:
        log_event(
            user_id=user_id,  
            device=device,     
            action="CheckID",
            topic="Signup_log",
            status="failed",
            error="ID already exists", # ID가 중복될 때 error 추가
            requested_id=username_check.id,
            ip_address= ip_address ### IP 있길래.. 필요없을까? 위치로 지역 같은거 추출가능하니까..? ###
        )
        raise HTTPException(status_code=400, detail="아이디가 이미 존재합니다.")
    log_event(
        user_id=user_id,  
        device=device,     
        action="CheckID",
        topic="Signup_log",
        status="success",
        error="None",
        requested_id=username_check.id,
        ip_address= ip_address
    )
    return {"is_taken": False}  # 아이디가 사용 가능함

# 회원가입 API
@router.post("/signup")
async def signup(request: Request, user: UserSignUp):

    user_id = "anonymous"  # 로그인 전에는 anonymous
    device = request.headers.get("User-Agent", "Unknown Device")
    ip_address = request.client.host  # 클라이언트 IP 주소

    # 저장 전 아이디 중복 체크 (백엔드에서 최종확인)
    existing_user = await user_collection.find_one({"id": user.id})
    if existing_user:
        log_event(
            user_id=user_id,
            device=device,
            action="SignUp ID check",
            topic="Signup_log",
            status="failed",
            error="ID already exists", # ID가 중복될 때 error 추가
            requested_id=user.id,
            ip_address=ip_address,
        )
        return {"is_taken": True} 
        
    
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

    try:
        # 사용자 정보 DB에 저장
        result = await user_collection.insert_one(user_data)
        
        # 회원가입 성공 시 로그 기록
        log_event(
            user_id=user_id,
            device=device,
            action="SignUp",
            topic="Signup_log",
            status="success",
            error="None",
            requested_id=user.id,
            ip_address=ip_address,
        )
        return {"success": True}
    
    except PyMongoError as e:
        # DB 저장 실패 시 로그 기록
        log_event(
            user_id=user_id,
            device=device,
            action="SignUp",
            topic="Signup_log",
            status="failed",
            error=f"DB 저장 실패: {str(e)}",
            requested_id=user.id,
            ip_address=ip_address,
            
        )  
        # 예외 처리: DB 저장 실패시 HTTP 500 오류 발생
        raise HTTPException(status_code=500, detail="회원가입 처리 중 DB저장 오류가 발생했습니다.")