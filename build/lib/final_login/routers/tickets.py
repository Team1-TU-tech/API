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
from src.final_login.db_model import user_collection


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
    request: Request, # 요청 객체 추가
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

    # if token:
    # # JWT 토큰 디코드
    #     try:
    #         decoded_token = verify_token(
    #             token=token,
    #             SECRET_KEY=SECRET_KEY,
    #             ALGORITHM=ALGORITHM,
    #             refresh_token=None,
    #             expires_delta=None
    #         )
    #         user_id = decoded_token.get("id", "anonymous")

    #         # 로그인한 경우 추가 정보 가져오기
    #         user_info = await user_collection.find_one({"id": user_id})
    #         if user_info:
    #             gender = user_info.get("gender")
    #             birthday = user_info.get("birthday")
    #         else:
    #             print(f"User not found for user_id: {user_id}")
    #     except JWTError as e:
    #         print(f"Token verification failed: {str(e)}")
    #         raise HTTPException(status_code=401, detail="Invalid token.")
    # else:
    #     print("No token provided. Proceeding as anonymous user.")

    if token:
        # 토큰이 KakaoToken인지 확인
        if "kakaoToken" in token.lower():  # KakaoToken인 경우
            try:
                # Kakao Token 검증
                kakao_user_info = verify_kakao_token(token)  # 아래 verify_kakao_token 함수 참조
                user_id = kakao_user_info.get("id", "anonymous")
            except HTTPException as e:
                print(f"Kakao token verification failed: {str(e)}")
                raise HTTPException(status_code=401, detail="Invalid Kakao token.")
        else:
            # 기존 JWT 디코딩 로직
            try:
                decoded_token = verify_token(
                    token=token,
                    SECRET_KEY=SECRET_KEY,
                    ALGORITHM=ALGORITHM,
                    refresh_token=None,
                    expires_delta=None
                )
                user_id = decoded_token.get("id", "anonymous")
            except JWTError as e:
                print(f"Token verification failed: {str(e)}")
                raise HTTPException(status_code=401, detail="Invalid token.")
    else:
        print("No token provided. Proceeding as anonymous user.")
        user_id = "anonymous"  # 기본값 설정

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

    cursor = collection.find(query)
    print(f"MongoDB Query: {query}")
    # MongoDB에서 검색

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
            if ticket_url and ticket_end_date>=today:
                on_sale = True
            else:
                on_sale = False
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
            user_id=user_id,  # JWT 토큰에서 추출한 user_id 사용
            device=device,     # 디바이스 정보 (User-Agent 또는 쿼리 파라미터)
            action="search",   # 액션 종류: 'Search'
            topic="search_log", #카프카 토픽 구별을 위한 컬럼
            category=category if category is not None else "None", # 카테고리
            region=region if region is not None else "None",
            keyword=keyword if keyword is not None else "None", 
            gender=gender, 
            birthday=birthday
            
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
    gender = None  # 기본W값
    birthday = None  # 기본값

    if token:
        # JWT 토큰 디코드
        try:
            decoded_token = verify_token(
                token=token,
                SECRET_KEY=SECRET_KEY,
                ALGORITHM=ALGORITHM,
                refresh_token=None,
                expires_delta=None
            )
            user_id = decoded_token.get("id", "anonymous")

            # 로그인한 경우 추가 정보 가져오기
            user_info = await user_collection.find_one({"id": user_id})
            if user_info:
                gender = user_info.get("gender")
                birthday = user_info.get("birthday")
            else:
                print(f"User not found for user_id: {user_id}")
        except JWTError as e:
            print(f"Token verification failed: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token.")
    else:
        print("No token provided. Proceeding as anonymous user.")
    #########################################################
   
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
                    gender=gender,  # 로그인하지 않았다면 None
                    birthday=birthday  # 로그인하지 않았다면 None
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
         