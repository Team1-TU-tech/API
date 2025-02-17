import os
import pymongo import MongoClient
from fastapi import APIRouter
from datetime import datetime, timedelta
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
smtp_port = 587
smtp_user = os.getenv("EMAIL_ID")
smtp_pw = os.getenv("EMAIL_PW")

def send_email(recipient, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

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
            <html>
                <body>
                    <h2>안녕하세요, {user_id}님!</h2>
                    <p><strong>'{title}'</strong>이/가 내일 오픈합니다! 🎉</p>
            
                    <ul>
                        <li><strong>오픈 날짜:</strong> {open_date}</li>
                        <li><strong>공연 날짜:</strong> {start_date} ~ {end_date}</li>
                        <li><strong>장소:</strong> {location}</li>
                    </ul>

                    <p>아래 링크를 클릭하여 공연 상세 정보를 확인해 보세요!</p>
                    <p>
                        <a href="http://localhost:3000/detail/{perform_id}" 
                        style="display:inline-block; padding:10px 20px; background:#007BFF; color:white; 
                          text-decoration:none; border-radius:5px;">
                        🔗 공연 상세 페이지로 이동
                        </a>
                    </p>

                    <p>감사합니다.<br><strong>Ticket Moa</strong></p>
                </body>
            </html>
            """
            send_email(user_email, email_subject, email_body)
           
    else:
        print(f"{perform.get('title')}의 open_date가 없습니다")

        



    



