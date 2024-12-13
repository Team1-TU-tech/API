#!/bin/bash

# 백그라운드에서 Kafka 컨슈머 실행
python /code/src/final_login/routes/consumer.py &

# FastAPI 애플리케이션 실행
uvicorn src.final_login.app:app --host 0.0.0.0 --port 8000
