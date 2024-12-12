from bson import ObjectId
from pydantic import BaseModel, Field, ValidationError
from io import BytesIO
from fastapi import FastAPI, HTTPException, APIRouter
from pymongo import MongoClient
from collections import Counter
from typing import List
import json
import boto3
import pandas as pd
import datetime
import os
from dotenv import load_dotenv  # 추가

load_dotenv()  # .env 파일에서 변수 로드

router = APIRouter()

# MongoDB 연결
client = MongoClient(os.getenv('MONGO_URI'))
db = client["tut"]
ticket_collection = db["ticket"]

aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
region_name=os.getenv("AWS_DEFAULT_REGION")

# S3에서 로그 읽기
s3_client = boto3.client('s3',
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        region_name=region_name
                        )

def get_logs(bucket_name: str = "t1-tu-data", directory: str = 'view_detail_log/') -> List[dict]:
    try:
        # S3에서 디렉토리 내 파일 목록 가져오기
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=directory)

        # 파일 목록을 가져왔는지 확인
        if 'Contents' not in response:
            print("No files found in the specified directory.")
            return []

        # Parquet 파일만 필터링
        parquet_files = [obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.parquet')]

        if not parquet_files:
            print("No Parquet files found.")
            return []

        # Parquet 파일을 읽어 pandas DataFrame으로 결합
        logs = []
        for file_key in parquet_files:
            try:
            # S3에서 Parquet 파일을 읽기
                print(f"Reading file: s3://{bucket_name}/{file_key}")
                obj = s3_client.get_object(Bucket=bucket_name, Key=file_key)
                # BytesIO를 사용하여 Parquet 파일을 pandas로 읽기
                parquet_data = BytesIO(obj['Body'].read())
                df = pd.read_parquet(parquet_data)  # pyarrow 또는 fastparquet 필요
                logs.append(df)
            except Exception as e:
                print(f"Error reading file {file_key}: {e}")
        
         # 전체 로그 데이터 결합
        all_logs = pd.concat(logs, ignore_index=True)

        # ticket_id 컬럼만 추출하여 리스트로 반환
        ticket_ids = all_logs['ticket_id'].tolist()

        return ticket_ids
        
    except Exception as e:
        print(f"Error reading from S3: {e}")
        return []

def get_top_tickets(ticket_ids: List[str], top_n: int = 8) -> List[str]:
    # ticket_id 카운트
    ticket_counter = Counter(ticket_ids)

    # 상위 top_n 개 ticket_id 추출
    top_ticket_ids = ticket_counter.most_common(top_n)

    return [ticket_id for ticket_id, _ in top_ticket_ids]

@router.get("/top_show")
async def top_tickets():
    # S3에서 로그 데이터 가져오기
    ticket_ids = get_logs()

    if not ticket_ids:
        raise HTTPException(status_code=404, detail="No logs found")

    # 상위 8개 ticket_id 추출
    top_ticket_ids = get_top_tickets(ticket_ids)

    # 상위 ticket_id에 해당하는 ticket 정보 가져오기
    top_ticket_info = []
    for ticket_id in top_ticket_ids:
        ticket_data = ticket_collection.find_one({"_id": ObjectId(ticket_id)})

        if ticket_data:
            ticket_info = {
                "title": ticket_data.get("title", ""),
                "start_date": ticket_data.get("start_date", ""),
                "end_date": ticket_data.get("end_date", ""),
                "poster_url": ticket_data.get("poster_url", ""),
                "location": ticket_data.get("location", "")
            }
            top_ticket_info.append(ticket_info)
        else:
            top_ticket_info.append({"ticket_id": ticket_id, "error": "Ticket not found in collection"})

    return {"top_tickets": top_ticket_info}