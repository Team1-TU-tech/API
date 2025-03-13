
from fastapi import HTTPException, APIRouter, Request
from pymongo import MongoClient
from bson import ObjectId
from pydantic import BaseModel
from typing import List
import datetime
from dotenv import load_dotenv
import os
from src.final_login.routers.like import *
from src.final_login.validate import *

load_dotenv()
router = APIRouter()

# MongoDB 클라이언트 설정
client = MongoClient(os.getenv("MONGO_URI"))
db = client["tut"]

# 컬렉션 참조
popular_collection = db["popular"]
collection = db["data"]

class TicketData(BaseModel):
    id: str
    title: str
    poster_url: str
    start_date: str
    end_date: str
    location: str
    category: str
    is_liked: bool

@router.get("/popular", response_model=List[TicketData])
async def get_popular_data(request: Request):
    
    try:
        ################# user_like collection과 연결 ####################################
         # 요청 헤더에서 user_id 가져오기
        user_info = await token_decode_verify(request=request)
        user_id = user_info["user_id"]
        #user_id = "3811135326"
        
        connect_like = connect_like_db()

        user_like_data = await connect_like.find_one({"user_id": user_id})

        # 좋아요한 공연 ID 리스트 추출
        liked_performance_ids = set()
        if user_like_data and isinstance(user_like_data,dict):  # 딕셔너리인지 확인
            performances = user_like_data.get("performances", [])  # get()을 사용해 접근
            if isinstance(performances, list):  # 리스트인지 확인
                liked_performance_ids = {p["id"] for p in performances if isinstance(p, dict) and "id" in p}
        ############################################################

        # 오늘 날짜 가져오기
        today = datetime.now().strftime("%Y.%m.%d")

        # end_date가 오늘 이후인 데이터 중 count 기준 내림차순 상위 8개 가져오기
        popular_docs = list(
            popular_collection.find(
                {},
                {"ticket_id": 1, "count": 1}
            ).sort("count", -1)
        )

        # ticket_id 리스트 추출
        ticket_ids = [ObjectId(doc["ticket_id"]) for doc in popular_docs if "ticket_id" in doc]

        # ticket_id에 해당하는 상세 데이터를 data 컬렉션에서 가져오기
        tickets = list(collection.find({"_id": {"$in": ticket_ids}, "end_date": {"$gte": today}}).limit(8)
        )
        ########################################################
        for ticket in tickets:
            performance_id = str(ticket["_id"])
            is_liked = performance_id in liked_performance_ids
            ticket["is_liked"] = is_liked
        ########################################################

        # Pydantic 모델로 변환
        popular = [
            TicketData(
                id=str(ticket["_id"]),
                title=ticket.get("title"),
                poster_url=ticket.get("poster_url"),
                start_date=ticket.get("start_date"),
                end_date=ticket.get("end_date"),
                location=ticket.get("location"),
                category=ticket.get("category"),
                is_liked=ticket.get("is_liked")
            )
            for ticket in tickets
        ]

        return popular

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")