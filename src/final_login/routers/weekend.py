from fastapi import FastAPI, APIRouter
from pymongo import MongoClient
from datetime import datetime, timedelta
from typing import List, Dict
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

mongo_uri = os.getenv("MONGO_URI")

# 비동기 MongoDB 클라이언트 설정
try:
    client = AsyncIOMotorClient(mongo_uri)
    db = client['tut']
    collection = db['data']

    print("MongoDB connected successfully!")
    
except Exception as e:
    print(f"MongoDB connection error: {e}")

# 이번 주 토요일과 일요일 날짜 계산
def get_this_weekend_dates():
    today = datetime.today()
    # 이번 주 토요일 (이번 주 시작일부터 +5일)
    saturday = today + timedelta(days=(5 - today.weekday()))
    # 이번 주 일요일 (토요일 + 1일)
    sunday = saturday + timedelta(days=1)
    
    # 날짜를 "YYYY.MM.DD" 형식의 문자열로 변환
    saturday_str = saturday.strftime('%Y.%m.%d')
    sunday_str = sunday.strftime('%Y.%m.%d')

    return saturday_str, sunday_str

# FastAPI 엔드포인트: 이번 주 주말에 공연 중인 공연들 반환
@router.get("/this_weekend", response_model=List[Dict[str, str]])
async def get_performances_this_weekend():
    # 이번 주 토요일과 일요일 날짜 구하기
    saturday, sunday = get_this_weekend_dates()

    # MongoDB에서 start_date가 이번 주 주말에 해당하는 공연들 조회
    performances_cursor = collection.find({
        "start_date": {
            "$gte": saturday,
            "$lte": sunday
        }
    })

    result = []
    async for performance in performances_cursor:
        result.append({
            "id": str(performance["_id"]),
            "title": performance["title"], 
            "category": performance['category'],
            "start_date": performance["start_date"], 
            "end_date": performance["end_date"],
            "poster_url": performance['poster_url'],
            "location": performance['location']
        })
    
    return result
