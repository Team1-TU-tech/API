from fastapi import APIRouter, HTTPException
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

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
    id: str
    title: Optional[str] = None
    poster_url: Optional[str] = None
    start_date: str
    end_date: str

# 배너에 표시할 티켓 데이터를 조회하는 API
@router.get("/banner", response_model=List[TicketData])
async def get_banner():
    try:
        # 현재 날짜 기준으로 가장 먼 start_date를 가진 티켓 11개 조회
        now = datetime.now().strftime("%Y.%m.%d")
        tickets = []
        
        async for ticket in collection.find(
            {"start_date": {"$gt": now}}  # 현재 날짜 이후의 티켓들
        ).sort("start_date", 1).limit(11):  # 내림차순으로 정렬하여 11개만 반환
            tickets.append(TicketData(
                id=str(ticket["_id"]),
                title=ticket.get("title"),
                poster_url=ticket.get("poster_url"),
                start_date=ticket.get("start_date"),
                end_date=ticket.get("end_date")
            ))
        
        return tickets
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching banner tickets: {str(e)}")