import logging
import os
import json
from datetime import datetime

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

# JSON 형식 로그 포맷터 설정
json_formatter = JsonFormatter()

def log_event(user_id: str, device: str, action: str, **kwargs):

    # 로그 메시지 생성
    log_message = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "device": device,
        "action": action,
        **kwargs
    }
 
    # 로그 기록
    logger.info(log_message)

    # 유니코드 문자열을 그대로 출력
    print("Logging event:", log_message)


