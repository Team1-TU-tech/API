from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from src.final_login.db_model import *
from src.final_login.validate import *
from src.final_login.routers.kakao import *
from bson import ObjectId
import os

mongo_uri = os.getenv("MONGO_URI")
router = APIRouter()

### 공연데이터 가져오기
def connect_perf_db():
    try:
        client = AsyncIOMotorClient(mongo_uri)
        db = client['tut']
        collection = db['data']
        print("MongoDB connected successfully!")
        
        return collection

    except Exception as e:
        print(f"MongoDB connection error: {e}")
    

def connect_like_db():
    try:
        client = AsyncIOMotorClient(mongo_uri)
        db = client['signup']
        collection = db['user_like']
        print("MongoDB connected successfully!")
        
        return collection

    except Exception as e:
        print(f"MongoDB connection error: {e}")

### 유저데이터 가져오기 
def connect_users_db():
    try:
        client = AsyncIOMotorClient(mongo_uri)
        db = client['signup']
        collection = db['users']
        print("MongoDB connected successfully!")
        
        return collection

    except Exception as e:
        print(f"MongoDB connection error: {e}")
    
async def get_all_users():
    collection = connect_users_db()

    if collection is None:
        print("MongoDB 연결에 실패했습니다. 데이터를 가져올 수 없습니다.")
        return [] 
    
    performances_cursor = collection.find({},{'id':1,'email': 1}).limit(100)
    performances = await performances_cursor.to_list(None)

    
    return performances


@router.post("/like")
async def click_like(request: Request, like_perf_id: LikePerfId):
    #token = request.headers.get("Authorization")
    #token ="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImFkbWluIiwiZXhwIjoxNzQwMzczMTk0fQ.0rBAc7EaGbuP-Rs7tp8inIReruYyku344nF60Ikz38M"
    perf_id = like_perf_id.id
   
    # DB에서 공연정보 가져오기
    connect_perf = connect_perf_db()
    performance_data = await connect_perf.find_one({"_id": ObjectId(perf_id)})
    connect_like = connect_like_db()
    
    if performance_data:
        # 필요한 필드를 포함한 데이터 준비
        data_to_insert = {
            "id": str(performance_data["_id"])
            #"title": performance_data["title"],
            #"start_date": performance_data["start_date"],
            #"end_date": performance_data["end_date"],
            #"poster_url": performance_data["poster_url"],
            #"location": performance_data["location"],
            #"open_date": performance_data["open_date"]
        }

        user_data = await connect_like.find_one({"user_id": "gamza"})
        
        if user_data:
            # performance_data가 이미 존재하는지 확인
            existing_performance = next((p for p in user_data["performances"] if p["id"] == str(perf_id)), None)
            if not existing_performance:
                # user_id가 이미 존재하는지 확인하고, 존재하면 해당 문서에 performance_data를 추가
                result = await connect_like.update_one(
                    {"user_id": "gamza"},  # user_id로 문서를 찾기
                {
                    "$push": {  # performance_data를 'performances'라는 배열 필드에 추가
                        "performances": data_to_insert
                    }
                
                },
                upsert = True
            )
            else:
                print("Performance data already exists, skipping insertion.")
        else:
            result = await connect_like.update_one(
                    {"user_id": "gamza",
                     "user_email": "test@gmail.com"},  # user_id로 문서를 찾기
                {
                    "$push": {  # performance_data를 'performances'라는 배열 필드에 추가
                        "performances": data_to_insert
                    }
                
                },
                upsert = True
            )
    
    return data_to_insert

@router.delete("/del_like")
async def del_like(request: Request, like_perf_id: LikePerfId):
    perf_id = like_perf_id.id
    connect_like = connect_like_db()
    
    # 삭제할 데이터를 검색하고 제거
    result = await connect_like.update_one(
        {"user_id": "gamza"},  # user_id로 문서를 찾음
        {
            "$pull": {  # performance_id가 일치하는 데이터를 배열에서 제거
                "performances": {"id": perf_id}
            }
        }
    )

    return perf_id

@router.get("/get_like")
async def get_like_performances(request: Request):
    user_id = "gamza"
    # MongoDB에서 ID에 해당하는 문서 찾기
    connect_like = connect_like_db()

    find_user = await connect_like.find_one({"user_id": user_id})
    if find_user:
        return find_user.get("performances", [])

    else:
        raise HTTPException(status_code=404, detail="User not found")

