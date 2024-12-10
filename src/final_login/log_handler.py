import logging
import os
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler

# 로거 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # 기본 로그 레벨 설정

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

# 로그 이벤트 함수 정의
def log_event(user_id: str, **kwargs):
    # 로그 메시지 생성
    log_message = {
        #"timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        **kwargs
    }

    
    # INFO 로그 기록
    logger.info(log_message)
