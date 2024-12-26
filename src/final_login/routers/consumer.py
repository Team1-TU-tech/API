from kafka import KafkaConsumer
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import boto3
import os, time
from io import BytesIO
from dotenv import load_dotenv

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
consumer.subscribe(['search_log', 'view_detail_log'])

# S3 클라이언트 설정
s3 = boto3.client('s3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name="ap-northeast-2"
    )


# 로그 데이터 소비 및 S3에 저장
def consume_and_save_to_s3(batch_size=100, timeout=10):
    log_messages = []
    start_time = time.time()
    
    while True:
        for message in consumer:
            log_messages.append(message.value)
            print(f"토픽: {message.topic}, 메시지: {message.value}")

            # 배치 크기나 시간 조건이 충족되지 않으면 계속 쌓기만 함
            if len(log_messages) < batch_size and time.time() - start_time < timeout:
                continue  # 조건이 맞을 때까지 기다림

            # 배치 크기나 시간이 되면 S3에 업로드
            df = pd.json_normalize(log_messages)  # JSON을 DataFrame으로 변환

            # DataFrame을 Parquet 형식으로 변환
            table = pa.Table.from_pandas(df)

            # 메모리 버퍼에 Parquet 파일을 저장
            buffer = BytesIO()
            pq.write_table(table, buffer)
            buffer.seek(0)  # 버퍼의 처음으로 이동

            # S3에 Parquet 파일 업로드
            timestamp = time.strftime("%Y-%m-%d_%H-%M")  # 초까지 포함한 타임스탬프 생성

            s3.put_object(
                Bucket='t1-tu-data',
                Key=f'{message.topic}/{timestamp}.parquet',
                Body=buffer
            )

            print(f'로그가 S3에 업로드되었습니다: {message.topic}/{timestamp}.parquet')

            # 배치 후 초기화
            log_messages = []
            start_time = time.time()  # 시간 초기화

        consumer.commit()  # 메시지를 처리한 후 수동으로 커밋

        # 잠시 대기 (소비가 너무 빠르지 않게)
        time.sleep(0.5)

if __name__ == '__main__':
    consume_and_save_to_s3(batch_size=100, timeout=10)

