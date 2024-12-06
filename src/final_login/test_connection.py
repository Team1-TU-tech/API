from pymongo.errors import ConnectionFailure
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB Atlas 연결 URI
client = AsyncIOMotorClient("mongodb+srv://hahahello777:VIiYTK9NobgeM1hk@cluster0.5vlv3.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0")
try:
    # MongoDB Atlas 클라이언트 연결

    # 연결 확인 (연결 성공 시 ping)
    client.admin.command('ping')
    print("MongoDB Atlas에 연결되었습니다.")

    # 데이터베이스 목록 확인
    print("데이터베이스 목록:")
    print(client.list_database_names())

except ConnectionFailure as e:
    print(f"MongoDB Atlas 연결 실패: {e}")
