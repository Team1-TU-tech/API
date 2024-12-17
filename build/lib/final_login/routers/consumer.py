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
consumer.subscribe(['Login_log', 'Logout_log', 'KakaoLogin_log', 'KakaoLogout_log', 'Signup_log', 'view_detail_log' , 'search_log'])

# S3 클라이언트 설정
s3 = boto3.client('s3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name="ap-northeast-2"
    )

# 로그 데이터 소비 및 S3에 저장


# def consume_and_save_to_s3(batch_size=100, timeout=10):
#     log_messages = []
#     start_time = None
    
#     while True:

#         for message in consumer:
#             log_messages.append(message.value)
#             print(f"토픽: {message.topic}, 메시지: {message.value}")
                        
#             # 첫 번째 메시지 수신 시 start_time 설정
#             if start_time is None:
#                 start_time = time.time()


#             ################# 각 토픽별로 time count 되게 변경 ####################
#             # 배치 크기나 시간 조건이 충족되지 않으면 계속 쌓기만 함
#             if len(log_messages) >= batch_size or time.time() - start_time >= timeout:
#                 break  # 배치가 다 차거나 시간이 초과되면 루프 종료

#         if len(log_messages) >= batch_size or time.time() - start_time >= timeout:
#             # 배치 크기나 시간이 되면 S3에 업로드
#             df = pd.json_normalize(log_messages)  # JSON을 DataFrame으로 변환

#             # DataFrame을 Parquet 형식으로 변환
#             table = pa.Table.from_pandas(df)

#             # 메모리 버퍼에 Parquet 파일을 저장
#             buffer = BytesIO()
#             pq.write_table(table, buffer)
#             buffer.seek(0)  # 버퍼의 처음으로 이동

#             # S3에 Parquet 파일 업로드

#             kst_time = datetime.utcnow() + timedelta(hours=9)
#             timestamp = kst_time.strftime("%Y-%m-%d_%H-%M-%S")  # 초까지 포함한 타임스탬프 생성

#             s3.put_object(
#                 Bucket='t1-tu-data',
#                 Key=f'{message.topic}/{timestamp}.parquet',
#                 Body=buffer
#             )

#             logger.info(f'*******로그가 S3에 업로드되었습니다: {message.topic}/{timestamp}.parquet*******')
#             logger.info(log_messages)

#             # 배치 후 초기화
#             log_messages = []
#             start_time = time.time()  # 시간 초기화

#         consumer.commit()  # 메시지를 처리한 후 수동으로 커밋

#         # 잠시 대기 (소비가 너무 빠르지 않게)
#         time.sleep(0.5)


def consume_and_save_to_s3(batch_size=100, timeout=10):
    # 각 토픽별로 메시지 및 타이머 초기화
    topic_start_times = {}
    topic_log_messages = {topic: [] for topic in consumer.subscription()}
    
    while True:
        for message in consumer:
            topic = message.topic
            log_messages = topic_log_messages[topic]

            # 첫 번째 메시지 수신 시 start_time 설정
            if topic not in topic_start_times:
                topic_start_times[topic] = time.time()

            log_messages.append(message.value)
            print(f"토픽: {topic}, 메시지: {message.value}")
            
            # 배치 크기나 시간 조건이 충족되지 않으면 계속 쌓기만 함
            if len(log_messages) >= batch_size or time.time() - topic_start_times[topic] >= timeout:
                # 배치 크기나 시간이 되면 S3에 업로드
                kst_time = datetime.utcnow() + timedelta(hours=9)
                timestamp = kst_time.strftime("%Y-%m-%d_%H-%M-%S")  # 초까지 포함한 타임스탬프 생성

                # DataFrame을 Parquet 형식으로 변환
                df = pd.json_normalize(log_messages)  # JSON을 DataFrame으로 변환
                table = pa.Table.from_pandas(df)
                
                # 메모리 버퍼에 Parquet 파일을 저장
                buffer = BytesIO()
                pq.write_table(table, buffer)
                buffer.seek(0)  # 버퍼의 처음으로 이동

                # Parquet 파일을 S3에 업로드
                s3.put_object(
                    Bucket='t1-tu-data',
                    Key=f'{topic}/{timestamp}.parquet',
                    Body=buffer
                )
                logger.info(f'*******로그가 S3에 업로드되었습니다: {message.topic}/{timestamp}.parquet*******')
                logger.info(log_messages)
                
                # 메시지와 시간 초기화
                topic_log_messages[topic] = []
                topic_start_times[topic] = time.time()  # 새로 첫 메시지가 도착하는 시간으로 초기화

            consumer.commit()  # 메시지를 처리한 후 수동으로 커밋
            time.sleep(0.5)  # 소비가 너무 빠르지 않게 잠시 대기

if __name__ == '__main__':
    consume_and_save_to_s3(batch_size=100, timeout=10)