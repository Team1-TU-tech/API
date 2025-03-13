from fastapi import APIRouter, Request
from datetime import datetime, timedelta
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from src.final_login.routers.like import *

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
@router.get("/this_weekend", response_model=List[Dict[str, Any]])
async def get_performances_this_weekend(request: Request):

    # 이번 주 토요일과 일요일 날짜 구하기
    saturday, sunday = get_this_weekend_dates()

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
   
    #print(f"[DEBUG] 좋아요한 공연 ID 목록: {liked_performance_ids}")
    
    # MongoDB에서 start_date가 이번 주 주말에 해당하는 공연들 조회
    performances_cursor = collection.find({
        "start_date": {
            "$gte": saturday,
            "$lte": sunday
        }
    })

    result = []
    async for performance in performances_cursor:
        if performance.get("poster_url"):
            performance_id = str(performance["_id"])
            is_liked = performance_id in liked_performance_ids 

            # print(f"[DEBUG] 공연 ID: {performance_id}, 제목: {performance['title']}, 좋아요 여부: {is_liked}")
            
            result.append({
                "id": performance_id,
                "title": performance["title"], 
                "category": performance['category'],
                "start_date": performance["start_date"], 
                "end_date": performance["end_date"],
                "poster_url": performance['poster_url'],
                "location": performance['location'],
                "is_liked": is_liked
            })
    
    return result
