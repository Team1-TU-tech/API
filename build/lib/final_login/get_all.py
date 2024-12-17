from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from bson import ObjectId  # MongoDB의 ObjectId 사용

# MongoDB 연결
client = MongoClient("mongodb+srv://hahahello777:NDWdS4f47d3uLnZ3@cluster0.5vlv3.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0")
db = client['test']  # 데이터베이스 이름
collection = db['test']  # 컬렉션 이름

# FastAPI 애플리케이션 생성
app = FastAPI()

# ID로 상세 조회
@app.get("/detail/{id}")
def get_detail_by_id(id: str):
    try:
        # ObjectId로 변환하여 쿼리 수행
        object_id = ObjectId(id)
        result = collection.find_one({"_id": object_id})
        
        if result:
            result['_id'] = str(result['_id'])
            return {"data": result}
        else:
            raise HTTPException(status_code=404, detail="Item not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")