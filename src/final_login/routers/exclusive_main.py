# from fastapi import HTTPException, APIRouter
# from bson import ObjectId
# from typing import List
# from dotenv import load_dotenv
# import os
# from pymongo import MongoClient
# import datetime

# load_dotenv()
# router = APIRouter()

# # MongoDB 연결 설정
# client = MongoClient(os.getenv('MONGO_URI'))  # MongoDB URI
# db = client['tut']  # 사용할 데이터베이스 이름
# collection = db['data']  # 사용할 컬렉션 이름

# def serialize_objectid(data):
#     """ObjectId를 문자열로 변환"""
#     if isinstance(data, ObjectId):
#         return str(data)
#     elif isinstance(data, list):
#         return [serialize_objectid(item) for item in data]
#     elif isinstance(data, dict):
#         return {key: serialize_objectid(value) for key, value in data.items()}
#     return data

# @router.get("/exclusive/main", response_model=List[dict])
# def get_limited_sales():
#     try:
#         current_date = datetime.datetime.now().strftime("%Y.%m.%d")
#         results = collection.aggregate([
#             {"$match": {"hosts": {"$size": 1},
#                         "end_date": {"$gt": current_date}
#             }},
#             {"$unwind": "$hosts"},
#             {"$group": {
#                 "_id": "$hosts.site_id",
#                 "items": {"$push": {
#                     "id": "$_id",
#                     "title": "$title",
#                     "start_date": "$start_date",
#                     "end_date": "$end_date",
#                     "poster_url": "$poster_url",
#                     "location": "$location",
#                     "category": "$category"
#                 }},
#             }},
#             {"$project": {"items": {"$slice": ["$items", 4]}}}
#         ])

#         # ObjectId를 문자열로 변환
#         results_list = list(results)
#         for group in results_list:
#             group["items"] = [serialize_objectid(item) for item in group["items"]]

#         return results_list

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

from fastapi import HTTPException, APIRouter, Request
from bson import ObjectId
from typing import List
from dotenv import load_dotenv
import os
from pymongo import MongoClient
import datetime
from src.final_login.routers.like import *
from src.final_login.validate import *

load_dotenv()
router = APIRouter()

# MongoDB 연결 설정
client = MongoClient(os.getenv('MONGO_URI'))  # MongoDB URI
db = client['tut']  # 사용할 데이터베이스 이름
collection = db['data']  # 사용할 컬렉션 이름

def serialize_objectid(data):
    """ObjectId를 문자열로 변환"""
    if isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, list):
        return [serialize_objectid(item) for item in data]
    elif isinstance(data, dict):
        return {key: serialize_objectid(value) for key, value in data.items()}
    return data

@router.get("/exclusive/main", response_model=List[dict])
async def get_limited_sales(request: Request):

    ######################################################################
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
            liked_performance_ids = {str(p["id"]) for p in performances if isinstance(p, dict) and "id" in p}
   ########################################################################
                                     
    try:
        current_date = datetime.now().strftime("%Y.%m.%d")
        results = collection.aggregate([
            {"$match": {"hosts": {"$size": 1},
                        "end_date": {"$gt": current_date}
            }},
            {"$unwind": "$hosts"},
            {"$group": {
                "_id": "$hosts.site_id",
                "items": {"$push": {
                    "id": "$_id",
                    "title": "$title",
                    "start_date": "$start_date",
                    "end_date": "$end_date",
                    "poster_url": "$poster_url",
                    "location": "$location",
                    "category": "$category"
                }},
            }},
            {"$project": {"items": {"$slice": ["$items", 4]}}}
        ])

        # ObjectId를 문자열로 변환
        results_list = list(results)    
        for group in results_list:
            ########################################################
            group["items"] = [serialize_objectid(item) for item in group["items"]]
            for item in group["items"]:
                performance_id = item.get("id")
                if performance_id:
                    is_liked = performance_id in liked_performance_ids
                    item["is_liked"] = is_liked
                
        return results_list

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
