from kafka import KafkaProducer
import logging
import json
from datetime import datetime
import os

# 로거 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # 로그 레벨을 INFO로 설정 (INFO, ERROR 등)

# JsonFormatter 클래스 정의
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_message = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage()
        }
        return json.dumps(log_message, ensure_ascii=False)

# Kafka 프로듀서 설정 (전역에서 한 번만 설정)
from dotenv import load_dotenv

# .env 파일을 로드하여 환경 변수를 읽기
load_dotenv()

# Kafka 서버 환경 변수에서 값을 읽음
KAFKA_SERVER = os.getenv("KAFKA_SERVER")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_SERVER,
    acks='all',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def log_event(user_id: str, device: str, action: str, topic: str, **kwargs):

    # 로그 메시지 생성
    log_message = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "device": device,
        "action": action,
        "topic": topic,
        **kwargs
    }
 
     # Kafka에 로그 메시지 전송
    producer.send(topic, log_message)
    producer.flush()
    print(f"로그 데이터가 '{topic}' 토픽에 전송 완료!")

    # 로그 기록
    #logger.info(log_message)

    # 유니코드 문자열을 그대로 출력
    print("Logging event:", log_message)


