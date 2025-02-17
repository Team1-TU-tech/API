from fastapi import APIRouter, HTTPException, Request
from typing import List, Optional
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from src.final_login.db_model import *
from datetime import datetime
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
    
def get_all_users():
    collection = connect_users_db()

    if collection is None:
        print("MongoDB 연결에 실패했습니다. 데이터를 가져올 수 없습니다.")
        return [] 
    
    performances = collection.find({},{'id': 1, 'email': 1})
    
    return list(performances)


@router.post("/like")
async def click_like(request: Request, like_perf_id: LikePerfId):
    token = Request.headers.get("Authorization")
    perf_id = Request.body.get("ID")

    if token:
        try:
            # JWT 형식인지 확인
            if "." in token and len(token.split(".")) == 3:
                # JWT 디코딩 로직
                try:
                    decoded_token = verify_token(
                        token=token,
                        SECRET_KEY=SECRET_KEY,
                        ALGORITHM=ALGORITHM,
                        refresh_token=None,
                        expires_delta=None
                    )
                    user_id = decoded_token.get("id", "anonymous")
                    user_info = await user_collection.find_one({"id": user_id})
                    if user_info:
                        gender = user_info.get("gender", None)
                        birthday = user_info.get("birthday", None)
                        email = user_info.get("email", None)
                except JWTError as e:
                    raise HTTPException(status_code=401, detail="Invalid JWT token.")
            else:
                # Step 1: Kakao API를 사용하여 사용자 정보 가져오기
                user_info = kakao_api.get_kakao_user_info(token)  # `token`이 access_token으로 전달됨
                #print("[DEBUG] User info fetched from Kakao API:", user_info)
                
                user_id = user_info["id"]
                email = user_info.get("kakao_account", {}).get("email", None)
                
                # Step 2: MongoDB에서 user_id 조회
                user = await kakao_collection.find_one({"user_id": user_id})  # MongoDB에서 user_id 조회
                
                if user:
                    gender = user.get("gender", None)
                    birthday = user.get("birthday", None)
                    email = user.get("email", None)
                else:
                    raise HTTPException(status_code=401, detail="User not found in Kakao collection")
                
        except HTTPException as e:
            raise HTTPException(status_code=401, detail="Token verification failed.")
    else:
        user_id = "anonymous"  # 기본값 설정

    # DB에서 공연정보 가져오기
    connect_perf = connect_perf_db()
    performance_data = connect_perf.find({"_id": ObjectId(perf_id)})

    connect_like = connect_like_db()

    if performance_data.get("_id"):

        # 필요한 필드를 포함한 데이터 준비
        data_to_insert = {
            "user_id": user_id,
            "user_email": email,
            "id": str(performance_data["_id"]),
            "title": performance_data["title"],
            "start_date": performance_data["start_date"],
            "end_date": performance_data["end_date"],
            "poster_url": performance_data["poster_url"],
            "location": performance_data["location"],
            "open_date": performance_data["open_date"]
        }

        # user_id가 이미 존재하는지 확인하고, 존재하면 해당 문서에 performance_data를 추가
        result = connect_like.update_one(
            {"user_id": user_id},  # user_id로 문서를 찾기
            {
                "$push": {  # performance_data를 'performances'라는 배열 필드에 추가
                    "performances": data_to_insert
                }
            }
        )

        # 만약 user_id가 존재하지 않으면 새 문서 삽입
        if result.matched_count == 0:
            # user_id가 없으면 새로 삽입
            connect_like.insert_one({
                "user_id": user_id,
                "user_email": email,
                "performances": [data_to_insert]  # 처음 삽입되는 performance_data는 배열로 추가
            })

@router.delete("/del_like")
async def del_like(request: Request, like_perf_id: LikePerfId):
    token = Request.headers.get("Authorization")
    perf_id = Request.body.get("ID")

    ####################### 유저 아이디 디코드 ############################
    if token:
        try:
            # JWT 형식인지 확인
            if "." in token and len(token.split(".")) == 3:
                # JWT 디코딩 로직
                try:
                    decoded_token = verify_token(
                        token=token,
                        SECRET_KEY=SECRET_KEY,
                        ALGORITHM=ALGORITHM,
                        refresh_token=None,
                        expires_delta=None
                    )
                    user_id = decoded_token.get("id", "anonymous")
                    user_info = await user_collection.find_one({"id": user_id})
                    if user_info:
                        gender = user_info.get("gender", None)
                        birthday = user_info.get("birthday", None)
                        email = user_info.get("email", None)
                except JWTError as e:
                    raise HTTPException(status_code=401, detail="Invalid JWT token.")
            else:
                # Step 1: Kakao API를 사용하여 사용자 정보 가져오기
                user_info = kakao_api.get_kakao_user_info(token)  # `token`이 access_token으로 전달됨
                #print("[DEBUG] User info fetched from Kakao API:", user_info)
                
                user_id = user_info["id"]
                email = user_info.get("kakao_account", {}).get("email", None)
                
                # Step 2: MongoDB에서 user_id 조회
                user = await kakao_collection.find_one({"user_id": user_id})  # MongoDB에서 user_id 조회
                
                if user:
                    gender = user.get("gender", None)
                    birthday = user.get("birthday", None)
                    email = user.get("email", None)
                else:
                    raise HTTPException(status_code=401, detail="User not found in Kakao collection")
                
        except HTTPException as e:
            raise HTTPException(status_code=401, detail="Token verification failed.")
    else:
        user_id = "anonymous"  # 기본값 설정
    ####################### 유저 아이디 디코드 ############################

    # DB에서 공연정보 가져오기
    connect_perf_db = connect_perf_db()
    performance_data = connect_perf_db.find({"_id": ObjectId(perf_id)})

    connect_like_db = connect_like_db()


    # 삭제할 데이터를 검색하고 제거
    result = connect_like_db.update_one(
        {"user_id": user_id},  # user_id로 문서를 찾음
        {
            "$pull": {  # performance_id가 일치하는 데이터를 배열에서 제거
                "performances": {"id": ObjectId(perf_id)}
            }
        }
    )

    if result.modified_count > 0:
        return {"status": "success", "message": "Performance data deleted successfully."}
    else:
        return {"status": "failure", "message": "Performance data not found or user_id does not exist."}
    

@router.get("/get_like/{user_id}")
async def get_like_performances(request: Request):
    # MongoDB에서 ID에 해당하는 문서 찾기
    connect_like_db = connect_like_db()
    token = Request.headers.get("Authorization")

    ####################### 유저 아이디 디코드 ############################
    if token:
        try:
            # JWT 형식인지 확인
            if "." in token and len(token.split(".")) == 3:
                # JWT 디코딩 로직
                try:
                    decoded_token = verify_token(
                        token=token,
                        SECRET_KEY=SECRET_KEY,
                        ALGORITHM=ALGORITHM,
                        refresh_token=None,
                        expires_delta=None
                    )
                    user_id = decoded_token.get("id", "anonymous")
                    user_info = await user_collection.find_one({"id": user_id})
                    if user_info:
                        gender = user_info.get("gender", None)
                        birthday = user_info.get("birthday", None)
                        email = user_info.get("email", None)
                except JWTError as e:
                    raise HTTPException(status_code=401, detail="Invalid JWT token.")
            else:
                # Step 1: Kakao API를 사용하여 사용자 정보 가져오기
                user_info = kakao_api.get_kakao_user_info(token)  # `token`이 access_token으로 전달됨
                #print("[DEBUG] User info fetched from Kakao API:", user_info)
                
                user_id = user_info["id"]
                email = user_info.get("kakao_account", {}).get("email", None)
                
                # Step 2: MongoDB에서 user_id 조회
                user = await kakao_collection.find_one({"user_id": user_id})  # MongoDB에서 user_id 조회
                
                if user:
                    gender = user.get("gender", None)
                    birthday = user.get("birthday", None)
                    email = user.get("email", None)
                else:
                    raise HTTPException(status_code=401, detail="User not found in Kakao collection")
                
        except HTTPException as e:
            raise HTTPException(status_code=401, detail="Token verification failed.")
    else:
        user_id = "anonymous"  # 기본값 설정
    ####################### 유저 아이디 디코드 ############################

    find_user = await connect_like_db.find_one({"user_id": user_id})

    if find_user is None:
        raise HTTPException(status_code=404, detail="Item not found")

    like_performances = user_id.get("performances", [])
    
    return like_performances

