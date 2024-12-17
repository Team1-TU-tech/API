from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List
from bson import ObjectId
from datetime import datetime

# FastAPI 애플리케이션 객체 생성
app = FastAPI()

# MongoDB 연결을 위한 클라이언트
client = AsyncIOMotorClient("mongodb+srv://hahahello777:NDWdS4f47d3uLnZ3@cluster0.5vlv3.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0")  # MongoDB 연결 URL (로컬 MongoDB) 
db = client['test']  # 데이터베이스 이름
collection = db['test']  # 컬렉션 이름

# Pydantic 모델 정의 (응답 형식)
class TicketData(BaseModel):
    poster_url: Optional[str]
    title: Optional[str]
    location: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    id: str
    isExclusive: bool
    onSale: bool 

# 날짜 문자열을 datetime 객체로 변환하는 함수
def parse_date(date_string: str) -> Optional[datetime]:
    try:
        return datetime.strptime(date_string, "%Y.%m.%d").strftime("%Y.%m.%d")
    except ValueError:
        return None

# API 엔드포인트 정의
@app.get("/search", response_model=List[TicketData])
async def search_tickets(
    title: Optional[str] = Query(None, alias="title"),
    category: Optional[str] = Query(None, alias="category"),
    region: Optional[str] = Query(None, alias="region"),
    start_date: Optional[str] = Query(None, alias="start_date"),
    end_date: Optional[str] = Query(None, alias="end_date"),
    artist_name: Optional[str] = Query(None, alias="artist_name")  # artist_name 검색 파라미터 추가
):

    # MongoDB 쿼리 조건 설정
    query = {}

    # 날짜 파싱
    if start_date:
        start_date = parse_date(start_date)
        if start_date:
            query["start_date"] = {"$lte": end_date}  
    
    if end_date:
        end_date = parse_date(end_date)
        if end_date:
            query["end_date"] = {"$gte": start_date}  

    if title:
        query["title"] = {"$regex": title, "$options": "i"}  # 대소문자 구분 없이 검색

    if category:
        query["category"] = category

    if region:
        query["region"] = region

    # artist_name 검색 조건 추가
    if artist_name:
        query["artist.artist_name"] = {"$regex": artist_name, "$options": "i"}  # artist_name을 대소문자 구분 없이 검색

    # MongoDB에서 쿼리 실행
    cursor = collection.find(query)
    kst = pytz.timezone('Asia/Seoul')
    today = datetime.today(kst)

    # 결과 반환
    tickets = []
    async for ticket in cursor:
        hosts = ticket.get("hosts", [])
        # 독점 판별
        isexclusive = len(hosts) <= 1
        ticket_url = any(host.get("ticket_url") is not None for host in hosts)
        end_date_str = ticket.get("end_date")
        try:
            ticket_end_date = datetime.strptime(end_date_str, "%Y.%m.%d")
            if ticket_url and ticket_end_date>=today:
                on_sale = True
            else:
                ons_sale = False
        except (ValueError, TypeError):
            on_sale = False

        ticket_data = {
            "poster_url": ticket.get("poster_url"),
            "title": ticket.get("title"),
            "location": ticket.get("location"),
            "start_date": ticket.get("start_date"),
            "end_date": ticket.get("end_date"),
            "id": str(ticket.get("_id")),
            "isExclusive": isexclusive,
            "onSale": on_sale
        }
        tickets.append(ticket_data)

    return tickets


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