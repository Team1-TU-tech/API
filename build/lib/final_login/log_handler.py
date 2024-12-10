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
    """
    로그를 기록하는 함수
    :param timestamp: 로그 수집 시간 정보
    :param user_id: 사용자 ID
    :param device: 디바이스 정보
    :param action: 액션 정보 (예: 검색, 상세 조회 등)
    :param kwargs: 추가적인 정보들 (예: 날짜, 키워드, 에러 등)
    """
    
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


