from kafka import KafkaConsumer
import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import boto3
import os, time
from io import BytesIO
from dotenv import load_dotenv
import logging

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
def consume_and_save_to_s3(batch_size=100, timeout=10):
    log_messages = []  # 수집된 메시지를 저장
    start_time = time.time()  # 시작 시간 기록

    while True:
        try:
            # Kafka 메시지 폴링
            records = consumer.poll(timeout_ms=500)
            if not records:
                logger.warning("Kafka에서 가져온 메시지가 없습니다.")
                continue

            logger.info(f"Kafka에서 {len(records)}개의 레코드를 가져옴.")

            # 메시지 처리
            for topic_partition, messages in records.items():
                for message in messages:
                    try:
                        log_messages.append(message.value)
                        logger.info(f"로그 추가됨: {message.value}")
                    except Exception as e:
                        logger.error(f"메시지 처리 오류: {e}")

            # 업로드 조건 확인
            if len(log_messages) >= batch_size or (time.time() - start_time) >= timeout:
                #logger.info(f"배치 크기: {len(log_messages)} / 타임아웃: {time.time() - start_time}")
                if log_messages:
                    try:
                        # DataFrame 생성
                        df = pd.json_normalize(log_messages)
                        logger.info(f"DataFrame 생성 성공:\n{df.head()}")

                        # Parquet 변환
                        buffer = BytesIO()
                        pq.write_table(pa.Table.from_pandas(df), buffer)
                        buffer.seek(0)

                        # S3 업로드
                        timestamp = time.strftime("%Y-%m-%d_%H-%M")
                        topic_name = messages[0].topic if messages else "unknown_topic"
                        response = s3.put_object(
                            Bucket='t1-tu-data',
                            Key=f'{topic_name}/{timestamp}.parquet',
                            Body=buffer
                        )
                        #logger.info(f"S3 업로드 응답: {response}")

                        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                            logger.info("S3 업로드 성공!")
                        else:
                            logger.error("S3 업로드 실패!")

                    except Exception as e:
                        logger.error(f"S3 업로드 오류: {e}")

                    # 초기화
                    log_messages = []
                    start_time = time.time()

        except KeyboardInterrupt:
            logger.info("프로그램 종료.")
            break
        except Exception as e:
            logger.error(f"오류 발생: {e}")



if __name__ == '__main__':
    consume_and_save_to_s3(batch_size=100, timeout=10)