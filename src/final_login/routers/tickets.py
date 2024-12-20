import pytz
from fastapi import APIRouter, Query, HTTPException, Request
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from src.final_login.log_handler import log_event
import os
from dotenv import load_dotenv
from src.final_login.validate import verify_token
from src.final_login.token import SECRET_KEY, ALGORITHM
from jose import JWTError
from src.final_login.db_model import user_collection, kakao_collection
from src.final_login.kakao_manager import KakaoAPI
kakao_api = KakaoAPI()

load_dotenv()  # .env 파일에서 변수 로드

mongo_uri = os.getenv("MONGO_URI")
router = APIRouter()

# MongoDB 연결을 위한 클라이언트
try:
    client = AsyncIOMotorClient(mongo_uri)
    db = client['tut']
    collection = db['ticket']
    print("MongoDB connected successfully!")

except Exception as e:
    print(f"MongoDB connection error: {e}")

# Pydantic 모델 정의
class TicketData(BaseModel):
    poster_url: Optional[str]
    title: Optional[str]
    location: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    id: str
    isExclusive: bool
    onSale: bool

# 날짜 문자열을 datetime 객체로 변환하는 함수
def parse_date(date_string: str) -> Optional[datetime]:
    try:
        return datetime.strptime(date_string, "%Y.%m.%d").strftime("%Y.%m.%d")
    except ValueError:
        return None


# 티켓 검색 API
@router.get("/search", response_model=List[TicketData])
async def search_tickets(
    request: Request,  # 요청 객체 추가
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    ############# 로그 데이터 및 JWT 디코딩 추가 ##############
    token = request.headers.get("Authorization")
    user_id = "anonymous"
    gender = None  # 기본값
    birthday = None  # 기본값
    email = None # 기본값

    print("[DEBUG] Authorization header:", token)

    if token:
        try:
            # JWT 형식인지 확인
            if "." in token and len(token.split(".")) == 3:
                # JWT 디코딩 로직
                try:
                    decoded_token = verify_token(
                        token=token,
                        SECRET_KEY=SECRET_KEY,
                        ALGORITHM=ALGORITHM,
                        refresh_token=None,
                        expires_delta=None
                    )
                    user_id = decoded_token.get("id", "anonymous")

                    user_info = await user_collection.find_one({"id": user_id})
                    if user_info:
                        gender = user_info.get("gender", None)
                        birthday = user_info.get("birthday", None)
                        email = user_info.get("email", None)

                except JWTError as e:
                    raise HTTPException(status_code=401, detail="Invalid JWT token.")
            else:
                # Step 1: Kakao API를 사용하여 사용자 정보 가져오기
                user_info = kakao_api.get_kakao_user_info(token)  # `token`이 access_token으로 전달됨
                #print("[DEBUG] User info fetched from Kakao API:", user_info)
                
                user_id = user_info["id"]
                email = user_info.get("kakao_account", {}).get("email", "Unknown")

                # Step 2: MongoDB에서 user_id 조회
                user = await kakao_collection.find_one({"user_id": user_id})  # MongoDB에서 user_id 조회

                if not user:
                    # 인증 실패: MongoDB에 사용자가 없을 경우 에러 반환
                    raise HTTPException(status_code=401, detail="User not found in Kakao collection")

           
        except HTTPException as e:
            raise HTTPException(status_code=401, detail="Token verification failed.")
    else:
        user_id = "anonymous"  # 기본값 설정

    # 로그를 위한 디바이스 정보 추출
    device = request.headers.get("User-Agent", "Unknown")
    query = {}

    # 카테고리 매핑 적용
    if category:
        categories = category.split("/")
        query["category"] = {"$in": categories}

    if start_date:
        start_date = parse_date(start_date)
        if start_date:
            query["start_date"] = {"$lte": end_date}

    if end_date:
        end_date = parse_date(end_date)
        if end_date:
            query["end_date"] = {"$gte": start_date}

    if region:
        query["region"] = region

    if keyword:
        query["$or"] = [
            {"title": {"$regex": keyword, "$options": "i"}},
            {"artist.artist_name": {"$regex": keyword, "$options": "i"}}
        ]

    # MongoDB에서 검색
    cursor = collection.find(query)
    print(f"MongoDB Query: {query}")

    # 한국 시간(KST) 기준으로 오늘 날짜 구하기
    kst = pytz.timezone('Asia/Seoul')
    today_date = datetime.now(kst)
    today = datetime.strftime(today_date, "%Y.%m.%d")

    tickets = []
    async for ticket in cursor:
        hosts = ticket.get("hosts", [])
        isexclusive = len(hosts) <= 1
        ticket_url = any(host.get("ticket_url") is not None for host in hosts)
        end_date_str = ticket.get('end_date')
        try:
            ticket_end_date = datetime.strptime(end_date_str, "%Y.%m.%d").strftime("%Y.%m.%d")
            # ticket_url이 존재하고, end_date가 오늘 이후일 때만 on_sale을 True로 설정
            on_sale = ticket_url and ticket_end_date >= today
        except (ValueError, TypeError) as e:
            print(f"Error parsing end_date: {e}")
            on_sale = False  # end_date 형식 오류시 on_sale은 False

        ticket_data = {
            "poster_url": ticket.get("poster_url"),
            "title": ticket.get("title"),
            "location": ticket.get("location"),
            "start_date": ticket.get("start_date"),
            "end_date": ticket.get("end_date"),
            "id": str(ticket.get("_id")),
            "isExclusive": isexclusive,
            "onSale": on_sale
        }
        tickets.append(ticket_data)

    try:
        log_event(
            user_id=user_id,  # JWT 혹은 카카오 토큰에서 추출한 user_id 사용
            device=device,     # 디바이스 정보 (User-Agent 또는 쿼리 파라미터)
            action="search",   # 액션 종류: 'Search'
            topic="search_log",  # 카프카 토픽 구별을 위한 컬럼
            category=category if category not in [None, ""] else "None",  # 카테고리
            region=region if region not in [None, ""] else "None",
            keyword=keyword if keyword not in [None, ""] else "None",
            gender=gender if gender not in [None, ""] else "None",
            birthday=birthday if birthday not in [None, ""] else "None",
            email=email if email not in [None, ""] else "None",
        )
        print("Log event should have been recorded.")
    except Exception as e:
        print(f"Error logging event: {e}")

    return tickets


# ID로 상세 조회
@router.get("/detail/{id}")
async def get_detail_by_id(request: Request, id: str):

    ############# 로그 데이터 및 JWT 디코딩 추가 ##############
    token = request.headers.get("Authorization")
    user_id = "anonymous"  # 기본값 설정
    gender = None  # 기본값
    birthday = None  # 기본값
    email = None # 기본값

    if token:
        try:
            # JWT 형식인지 확인
            if "." in token and len(token.split(".")) == 3:
                # JWT 디코딩 로직
                try:
                    decoded_token = verify_token(
                        token=token,
                        SECRET_KEY=SECRET_KEY,
                        ALGORITHM=ALGORITHM,
                        refresh_token=None,
                        expires_delta=None
                    )
                    user_id = decoded_token.get("id", "anonymous")

                    # 추가 사용자 정보 가져오기
                    user_info = await user_collection.find_one({"id": user_id})
                    if user_info:
                        gender = user_info.get("gender", None)
                        birthday = user_info.get("birthday", None)
                        email = user_info.get("email", None)
                    else:
                        print(f"[DEBUG] User not found for user_id: {user_id}")
                except JWTError as e:
                    raise HTTPException(status_code=401, detail="Invalid JWT token.")
            else:
                # Kakao API를 사용하여 사용자 정보 가져오기
                user_info = kakao_api.get_kakao_user_info(token)
                #print("[DEBUG] User info fetched from Kakao API:", user_info)

                if "id" not in user_info:
                    raise HTTPException(status_code=401, detail="Invalid Kakao access_token")

                user_id = user_info["id"]

                # MongoDB에서 user_id 조회
                user = await kakao_collection.find_one({"user_id": user_id})
                if user:
                    gender = user.get("gender", None)
                    birthday = user.get("birthday", None)
                    email = user.get("email", None)
                else:
                    raise HTTPException(status_code=401, detail="User not found in Kakao collection")
        except HTTPException as e:
            print(f"[DEBUG] Token verification failed: {str(e)}")
            raise HTTPException(status_code=401, detail="Token verification failed.")
        except Exception as e:
            print(f"[DEBUG] Unexpected error during token verification: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error during authentication.")
    else:
        print("[DEBUG] No token provided. Proceeding as anonymous user.")

    #####################################################################################################    
   
    device = request.headers.get("User-Agent", "Unknown")

    try:
        object_id = ObjectId(id)
        result = await collection.find_one({"_id": object_id})

        if result:
            result['_id'] = str(result['_id'])

            # 로그 기록
            try:
                log_event(
                    user_id=user_id,  # 헤더에서 받은 user_id 또는 "anonymous"
                    device=device,     # 디바이스 정보 (User-Agent)
                    action="view_detail",  # 액션 종류: 'view_detail'
                    topic="view_detail_log",  # Kafka 토픽 구별을 위한 컬럼
                    ticket_id=result['_id'],
                    title=result.get('title', "None"),
                    category=result.get('category', "None"),  # 카테고리
                    region=result.get('region', "None"),  # 지역
                    gender=gender if gender not in [None, ""] else "None",
                    birthday=birthday if birthday not in [None, ""] else "None",
                    email=email if email not in [None, ""] else "None",
                )
                print("Log event recorded successfully.")
            except Exception as e:
                print(f"Error logging event: {e}")

            return {"data": result}
        else:
            raise HTTPException(status_code=404, detail="Item not found")
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")
         