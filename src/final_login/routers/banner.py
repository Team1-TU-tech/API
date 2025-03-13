# from fastapi import APIRouter, HTTPException
# from typing import List, Optional
# from pydantic import BaseModel
# from motor.motor_asyncio import AsyncIOMotorClient
# from datetime import datetime
# import os

# mongo_uri = os.getenv("MONGO_URI")
# router = APIRouter()

# # MongoDB 연결을 위한 클라이언트
# try:
#     client = AsyncIOMotorClient(mongo_uri)
#     db = client['tut']
#     collection = db['data']
#     print("MongoDB connected successfully!")
# except Exception as e:
#     print(f"MongoDB connection error: {e}")

# # Pydantic 모델 정의
# class TicketData(BaseModel):
#     id: str
#     title: Optional[str] = None
#     poster_url: Optional[str] = None
#     start_date: str
#     end_date: str
#     category: str

# # 배너에 표시할 티켓 데이터를 조회하는 API
# @router.get("/banner", response_model=List[TicketData])
# async def get_banner():
#     try:
#         # 현재 날짜 기준으로 가장 먼 start_date를 가진 티켓 11개 조회
#         now = datetime.now().strftime("%Y.%m.%d")
#         tickets = []
        
#         async for ticket in collection.find(
#             {"start_date": {"$gt": now}}  # 현재 날짜 이후의 티켓들
#         ).sort("start_date", 1).limit(11):  # 내림차순으로 정렬하여 11개만 반환
#             tickets.append(TicketData(
#                 id=str(ticket["_id"]),
#                 title=ticket.get("title"),
#                 poster_url=ticket.get("poster_url"),
#                 start_date=ticket.get("start_date"),
#                 end_date=ticket.get("end_date"),
#                 category=ticket.get("category")
#             ))
        
#         return tickets
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching banner tickets: {str(e)}")


from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional, Any
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from final_login.routers.like import connect_like_db
from final_login.validate import token_decode_verify

mongo_uri = os.getenv("MONGO_URI")
router = APIRouter()

# MongoDB 연결을 위한 클라이언트
try:
    client = AsyncIOMotorClient(mongo_uri)
    db = client['tut']
    collection = db['data']
    print("MongoDB connected successfully!")
except Exception as e:
    print(f"MongoDB connection error: {e}")

# Pydantic 모델 정의
class TicketData(BaseModel):
    id: str
    title: Optional[str] = None
    poster_url: Optional[str] = None
    start_date: str
    end_date: str
    category: str
    is_liked: bool
    
# 배너에 표시할 티켓 데이터를 조회하는 API
@router.get("/banner", response_model=List[TicketData])
async def get_banner(request: Request):
    try:
        # 현재 날짜 기준으로 가장 먼 start_date를 가진 티켓 11개 조회
        now = datetime.now().strftime("%Y.%m.%d")
        tickets = []

        # 요청 헤더에서 user_id 가져오기
        user_info = await token_decode_verify(request=request)
        user_id = user_info["user_id"]
        #user_id = "3811135326"

        connect_like = connect_like_db()

        user_like_data = await connect_like.find_one({"user_id": user_id})

        # 좋아요한 공연 ID 리스트 추출
        liked_performance_ids = set()
        if user_like_data and isinstance(user_like_data, dict):  # 딕셔너리인지 확인
            performances = user_like_data.get("performances", [])  # get()을 사용해 접근
            if isinstance(performances, list):  # 리스트인지 확인
                liked_performance_ids = {p["id"] for p in performances if isinstance(p, dict) and "id" in p}
        
        async for ticket in collection.find(
            {"start_date": {"$gt": now}}  # 현재 날짜 이후의 티켓들
        ).sort("start_date", 1).limit(11):  # 내림차순으로 정렬하여 11개만 반환
            
            ticket_id_str = str(ticket["_id"])  # ObjectId를 문자열로 변환
            is_liked = ticket_id_str in liked_performance_ids  # 좋아요한 ID와 비교
            
            tickets.append(TicketData(
                id=ticket_id_str,
                title=ticket.get("title"),
                poster_url=ticket.get("poster_url"),
                start_date=ticket.get("start_date"),
                end_date=ticket.get("end_date"),
                category=ticket.get("category"),
                is_liked=is_liked
            ))
        
        return tickets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching banner tickets: {str(e)}")