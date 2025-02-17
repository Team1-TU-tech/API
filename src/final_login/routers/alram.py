import os
import pymongo import MongoClient
from fastapi import APIRouter
from datetime import datetime, timedelta
from dotenv import load_dotenv

router = APIRoute
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client['signup']
collection = db['user_like']

# 오늘 기준으로 내일 날짜 계산
today = datetime.today()
tomorrow = today + timedelta(days=1)
tomorrow_str = tomorrow.strftime('%Y.%m.%d')

# open_date가 내일인 데이터 조회
performs = collection.find({
    "$expr": {
        "$eq": [
            {"$substr": ["$open_date", 0, 10]},  # open_date의 앞 10자 (YYYY.MM.DD)
            tomorrow_str
        ]
    }
})

# SMTP 설정
smtp_sever = "smtp.gmail.com"
smtp_port = 578
smtp_user = os.getenv("EMAIL_ID")
smtp_pw = os.getenv("EMAIL_PW")

def send_email(recipient, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(smtp_server, smtp_port) as s:
            s.starttls()
            s.login(smtp_user, smtp_pw)
            s.sendmail(smtp_user, recipient, msg.as_string())

        print(f"{recipient}에게 이메일 전송 완료")

    except Exception as e:
        print(f"전송 실패: {recipient}")

# 이메일 전송
for perform in performs:
    if perform.get('open_date'):
        perform_id = perform['object_id']
        user_id = perform['user_id']
        user_email = perform.get('email_id')
        title = perform['title']
        start_date = perform['start_date']
        end_date = perform['end_date']
        location = perform['location']
        open_date = perform['open_date']

        if user_email:
            email_subject = f"🔔{title} 오픈 알림🔔"
            email_body = f"""
            안녕하세요 {user_id}님! 
            '{title}'이/가 내일 오픈 합니다!

            오픈 날짜: {open_date}
            공연 날짜: {start_date} ~ {end_date}
            장     소: {location}

            아래 링크로 사이트를 방문하여 확인해 보세요 !
            localhost:3000/detail/{perform_id}

            감사합니다.
            Ticket Moa
            """

            send_email(user_email, email_subject, email_body)
           
    else:
        print(f"{perform.get('title')}의 open_date가 없습니다")

        



    



