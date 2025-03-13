from typing import List
from fastapi import HTTPException, APIRouter, Request
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import os
from src.final_login.routers.like import *
from src.final_login.validate import *
# from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()  # .env 파일에서 변수 로드
router = APIRouter()

# MongoDB 연결
client = MongoClient(os.getenv('MONGO_URI'))
db = client["tut"]
collection = db["data"]

# API 정의
@router.get("/exclusive/all", response_model=List[dict])
async def get_exclusive_sales(request: Request, site_id: int = None):
    try:
        # 오늘 날짜 가져오기
        current_date = datetime.now().strftime("%Y.%m.%d")

        # MongoDB에서 데이터 필터링
        #query = {"hosts": {"$size": 1}, "end_date": {"$gt": current_date}}
        query = {
            "$and": [
                {"end_date": {"$gt": current_date}},
                {"$expr": {"$eq": [{"$size": "$hosts"}, 1]}}
            ]
        }

        ################# user_like collection과 연결 ####################################
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
        ############################################################

        # MongoDB에서 데이터 필터링
        if site_id is not None:
            query["hosts"] = {"$elemMatch": {"site_id": site_id}}

        results = collection.find(query)

        exclusive_data = []
        for result in results:
            hosts = result.get("hosts", [])
            host = hosts[0]
            ticket_url = any(host.get("ticket_url") is not None for host in hosts)
            end_date_str = result.get('end_date')
            ####################################################
            performance_id = str(result["_id"])
            is_liked = performance_id in liked_performance_ids
            ####################################################

            try:
                ticket_end_date = datetime.strptime(end_date_str, "%Y.%m.%d").strftime("%Y.%m.%d")
                # ticket_url이 존재하고, end_date가 오늘 이후일 때만 on_sale을 True로 설정
                if ticket_url and ticket_end_date>=current_date:
                    on_sale = True
                else:
                    on_sale = False
            except (ValueError, TypeError) as e:
                if ticket_url and isinstance(end_date_str, str) and end_date_str == "상시공연":
                    on_sale = True
                else:
                    print(f"Error parsing end_date: {e}")
                    on_sale = False  # end_date 형식 오류시 on_sale은 False

            exclusive_data.append({
                "id": str(result.get("_id")),
                "title": result.get("title"),
                "start_date": result.get("start_date"),
                "end_date": result.get("end_date"),
                "poster_url": result.get("poster_url"),
                "location": result.get("location"),
                "category": result.get("category"),
                "onSale": on_sale,
                "is_liked": is_liked
            })

        if not exclusive_data:
            raise HTTPException(status_code=404, detail="No exclusive sales data found.")

        return exclusive_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
