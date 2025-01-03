from typing import List
from fastapi import HTTPException, APIRouter
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
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
        current_date = datetime.now().strftime("%Y.%m.%d")

        # MongoDB에서 데이터 필터링
        #query = {"hosts": {"$size": 1}, "end_date": {"$gt": current_date}}
        query = {
            "$and": [
                {"end_date": {"$gt": current_date}},
                {"$expr": {"$eq": [{"$size": "$hosts"}, 1]}}
            ]
        }

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
                "onSale": on_sale
            })

        if not exclusive_data:
            raise HTTPException(status_code=404, detail="No exclusive sales data found.")

        return exclusive_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

