from typing import List
from fastapi import FastAPI, HTTPException, APIRouter
from pymongo import MongoClient
from dotenv import load_dotenv
import datetime
import os

load_dotenv()  # .env 파일에서 변수 로드
router = APIRouter()

# MongoDB 연결
client = MongoClient(os.getenv('MONGO_URI'))
db = client["tut"]
collection = db["data"]

# API 정의
@router.get("/exclusive/all", response_model=List[dict])
def get_exclusive_sales(site_id: int = None):
    try:
        # 오늘 날짜 가져오기
        current_date = datetime.datetime.now().strftime("%Y.%m.%d")

        # MongoDB에서 데이터 필터링
        query = {"hosts": {"$size": 1}, "end_date": {"$gt": current_date}}
        # MongoDB에서 데이터 필터링
        if site_id is not None:
            query["hosts"] = {"$elemMatch": {"site_id": site_id}}

        results = collection.find(query)

        exclusive_data = []
        for result in results:
            host = result.get("hosts", [])[0]  # 첫 번째 host 가져오기

            exclusive_data.append({
                "id": str(result.get("_id")),
                "title": result.get("title"),
                "start_date": result.get("start_date"),
                "end_date": result.get("end_date"),
                "poster_url": result.get("poster_url"),
                "location": result.get("location"),
                "category": result.get("category")
            })

        if not exclusive_data:
            raise HTTPException(status_code=404, detail="No exclusive sales data found.")

        return exclusive_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

