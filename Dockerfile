# 베이스 이미지로 python 3.11 사용
FROM python:3.11

# 작업 디렉토리 설정
WORKDIR /code

# 필요 패키지 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 소스 코드 복사
COPY ./src /code/src

# start.sh 스크립트를 복사하고 실행 권한 부여
COPY ./start.sh /code/start.sh
RUN chmod +x /code/start.sh

# 스크립트를 실행
CMD ["/code/start.sh"]