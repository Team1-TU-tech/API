from kafka import KafkaConsumer
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import boto3
import os, time
from io import BytesIO
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import threading

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# .env 파일을 로드하여 환경 변수 읽기
load_dotenv()

KAFKA_SERVER = os.getenv("KAFKA_SERVER")

# Kafka consumer 설정
consumer = KafkaConsumer(
    #'logs',
    bootstrap_servers=KAFKA_SERVER,
    group_id='log-consumer-group',
    enable_auto_commit=False,  # 수동 오프셋 커밋 설정
    auto_offset_reset='latest',  # 'earliest' 또는 'latest' 설정
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)
# 여러 토픽을 구독
consumer.subscribe(['Validate', 'Login_log', 'Logout_log', 'KakaoLogin_log', 'KakaoLogout_log', 'Signup_log', 'View_detail_log' , 'Search_log'])

# S3 클라이언트 설정
s3 = boto3.client('s3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name="ap-northeast-2"
    )

# 각 토픽에 대한 메시지와 타이머를 저장하는 딕셔너리
topics_data = {}
countdown_timers = {}

# 토픽별 메시지 수
topic_message_count = {}
total_message_count = 0  # 모든 토픽의 메시지 합산 카운트

# 메시지를 수신하고 처리하는 함수
def consume_message(message):

    global total_message_count

    topic = message.topic
    log_message = message.value

    # 각 토픽별로 메시지 처리 시작
    if topic not in topics_data:
        topics_data[topic] = []
        topic_message_count[topic] = 0  # 카운트를 초기화

    # 새로운 메시지를 쌓는다
    topics_data[topic].append(log_message)
    topic_message_count[topic] += 1  # 메시지 수 카운트
    total_message_count += 1  # 전체 메시지 수 카운트 증가
    
    # 첫 번째 메시지일 경우 카운트다운 시작
    if topic not in countdown_timers or not countdown_timers[topic].is_alive():
        countdown_timers[topic] = threading.Timer(3600.0, upload_to_s3, args=[topic])
        countdown_timers[topic].start()

    # # 메시지가 추가될 때마다 타이머를 새로 시작해서 60초 후에 업로드
    # countdown_timers[topic].cancel()
    # countdown_timers[topic] = threading.Timer(60.0, upload_to_s3, args=[topic])
    # countdown_timers[topic].start()

    # 메시지 수가 1000개 이상이면 각 토픽으로 S3에 업로드
    if total_message_count >= 1000:
        upload_all_to_s3()


# S3에 업로드하는 함수 (모든 토픽에 대해 업로드)
def upload_all_to_s3():
    global total_message_count

    for topic, log_messages in topics_data.items():
        if log_messages:  # 메시지가 있을 때만 업로드
            upload_to_s3(topic)

    # 모든 토픽 업로드 후 전체 메시지 수 초기화
    total_message_count = 0

    
# S3에 업로드하는 함수
def upload_to_s3(topic):
    global total_message_count

    # 업로드할 메시지를 가져오기
    log_messages = topics_data[topic]
    num_messages = len(log_messages)  # 업로드한 메시지 수

    # DataFrame으로 변환
    df = pd.json_normalize(log_messages)

    # DataFrame을 Parquet 형식으로 변환
    table = pa.Table.from_pandas(df)

    # 메모리 버퍼에 Parquet 파일을 저장
    buffer = BytesIO()
    pq.write_table(table, buffer)
    buffer.seek(0)  # 버퍼의 처음으로 이동

    # 현재 시간을 기준으로 타임스탬프 생성
    kst_time = datetime.utcnow() + timedelta(hours=9)
    timestamp = kst_time.strftime("%Y-%m-%d_%H-%M")  # 분 포함한 타임스탬프 생성

    # S3 업로드
    s3.put_object(
        Bucket='t1-tu-data',
        Key=f'logs/{topic}/{timestamp}.parquet',  # 각 토픽별로 경로를 다르게 설정
        Body=buffer
    )

    # 업로드 후 초기화
    logger = logging.getLogger()
    logger.info(f'🐢🐢🐢🐢🐢🐢🐢🐢🐢🐢 로그가 S3에 업로드되었습니다: logs/{topic}/{timestamp}.parquet 🐢🐢🐢🐢🐢🐢🐢🐢🐢🐢')

    # 업로드한 메시지와 카운트 초기화
    topics_data[topic] = []  # 메시지 초기화
    topic_message_count[topic] = 0  # 메시지 수 초기화
    
    total_message_count -= num_messages # 이미 처리된 메세지가 합산 기준에 포함되어 중복 업로드가 이루어지지 않게끔끔

    if topic in countdown_timers:
        countdown_timers[topic].cancel()  # 타이머 초기화
        del countdown_timers[topic]

# 메시지 수신 및 처리 시작
for message in consumer:
    consume_message(message)