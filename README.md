# Kafka Setup

0.3.0/logging_kafka에서는 Docker Compose를 사용하여 Kafka와 관련 서비스를 실행합니다.
또한, consumer.py를 추가하여 로깅 메시지를 각 토픽으로 보내고, 이를 Kafka Consumer를 통해 처리하여 S3에 저장하는 기능을 구현하였습니다.

## 주요 변경 사항 
### 1. Docker Compose 기반 Kafka와 관련 서비스 실행
- Kafka 브로커(3개), Zookeeper, Kafka UI, FastAPI 애플리케이션 등을 포함하여 구성.
- FastAPI 애플리케이션은 Docker Compose를 통해 Kafka 및 관련 서비스와 함께 실행.

### 2. Kafka Consumer 및 S3 연동
- consumer.py를 통해 Kafka에서 메시지를 소비하여 S3에 저장하는 기능 추가.

### 3. Logging 메시지 전송
- FastAPI 애플리케이션에서 발생한 이벤트를 Kafka 토픽으로 전송하여 중앙화된 로그 관리 구현.
