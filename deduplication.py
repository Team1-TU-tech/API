from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os

load_dotenv()

def deduplication():

    # MongoDB에 연결
    client = MongoClient(os.getenv('MONGO_URI'))
    db = client["tut"]  # 데이터베이스 이름
    collection = db["ticket"]  # 컬렉션 이름

    # 1단계: 중복된 title을 찾고, hosts 배열의 크기가 2인 문서는 제외하기
    pipeline = [
        # 중복된 title을 그룹화하여 해당 문서들의 _id와 hosts 배열을 수집
        {
            "$group": {
                "_id": "$title",  # title을 기준으로 그룹화
                "count": { "$sum": 1 },
                "documents": { "$push": "$_id" },
                "hosts": { "$first": "$hosts" }  # 첫 번째 문서의 hosts 배열을 가져옴
            }
        },
        # 2단계: 중복된 title만 찾기 (count > 1)
        {
            "$match": {
                "count": { "$gt": 1 }  # 중복된 title만 필터링
            }
        }
    ]

    # 중복된 title을 가진 문서들의 _id를 찾음
    duplicates = collection.aggregate(pipeline)

    # 2단계: 중복된 문서 중 hosts 배열의 크기가 2인 문서는 제외
    ids_to_delete = []
    for doc in duplicates:
        title = doc["_id"]
        documents = doc["documents"]
        hosts = doc["hosts"]
        
        # hosts 배열의 크기가 2인 문서는 삭제에서 제외
        if len(hosts) >= 2:
            # documents 배열에서 첫 번째 문서를 제외하고 나머지 문서들 삭제 대상으로 추가
            ids_to_delete.extend(documents[1:])

    # 3단계: 중복된 문서들 삭제
    if ids_to_delete:
        # deleteMany를 사용하여 중복된 문서들 삭제
        result = collection.delete_many({
            "_id": { "$in": [ObjectId(id) for id in ids_to_delete] }
        })
        print(f"{result.deleted_count} 문서가 삭제되었습니다.")
    else:
        print("삭제할 문서가 없습니다.")

