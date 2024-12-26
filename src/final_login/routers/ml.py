from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from typing import List
from dotenv import load_dotenv
import os

load_dotenv()
router = APIRouter()

# MongoDB 연결 설정
client = AsyncIOMotorClient(os.getenv('MONGO_URI'))  # MongoDB URI
db = client['tut']  # 사용할 데이터베이스 이름
collection = db['similar']  # 사용할 컬렉션 이름

# ObjectId를 처리할 수 있도록 Pydantic 모델에 커스텀 변환 추가
class ObjectIdStr(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return str(ObjectId(v))

# similar_performances 반환 모델
class SimilarPerformance(BaseModel):
    id: str
    title: str
    location: str
    start_date: str
    end_date: str
    poster_url: str
    category: str

# 요청에 대한 모델 정의
class Item(BaseModel):
    id: str

@router.get("/recommendation/{id}", response_model=List[SimilarPerformance])
async def get_similar_performances(id: str):
    # MongoDB에서 ID에 해당하는 문서 찾기
    document = await collection.find_one({"_id": ObjectId(id)})

    if document is None:
        raise HTTPException(status_code=404, detail="Item not found")

    # 'similar_performances' 필드 반환
    similar_performances = document.get("similar_performances", [])

    for performance in similar_performances:
        performance["id"] = str(performance["_id"])
        performance.pop("_id",None)
    
    return similar_performances

