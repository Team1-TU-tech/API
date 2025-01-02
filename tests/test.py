import boto3
import pandas as pd
import pyarrow.parquet as pq
from io import BytesIO
from dotenv import load_dotenv
import os

load_dotenv()

# AWS S3 접근 설정
aws_access_key = os.getenv("AWS_ACCESS_KEY_ID") # AWS Access Key
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY") # AWS Secret Key
bucket_name = "t1-tu-data"
#prefix = "logs/KakaoLogin_log/"
#prefix = "logs/KakaoLogout_log/"
#prefix = "logs/Login_log/"
#prefix = "logs/Logout_log/"
#prefix = "logs/Signup_log/"
prefix = "logs/Search_log/"
#prefix = "logs/View_detail_log/"
#prefix = "logs/Login_log"




# S3 클라이언트 생성
s3 = boto3.client('s3',
                  aws_access_key_id=aws_access_key,
                  aws_secret_access_key=aws_secret_key)

# S3 객체 리스트 가져오기
response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
parquet_files = [obj['Key'] for obj in response.get('Contents', []) if obj['Key'].endswith('.parquet')]

# Parquet 파일 불러오기 및 JSON 변환
json_data_list = []

for file in parquet_files:
    response = s3.get_object(Bucket=bucket_name, Key=file)
    data = response['Body'].read()
    
    # Parquet 데이터를 데이터프레임으로 읽기
    parquet_data = pq.read_table(BytesIO(data))
    df = parquet_data.to_pandas()
    
    # JSON 형식으로 변환
    json_data = df.to_json(orient='records', lines=True)  # line-separated JSON
    json_data_list.append(json_data)

# 결과 출력
for i, json_data in enumerate(json_data_list):
    print(f"File {i + 1}:\n{json_data}\n")