import os
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# MongoDB 연결
load_dotenv()
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
    "performances.open_date": {"$regex": f"^{tomorrow_str}"}
})

# SMTP 설정
smtp_server = "smtp.naver.com"
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
        print(f"전송 실패: {recipient}, 오류 내용: {e}")

# 이메일 전송
for perform in performs:
    user_id = perform.get('user_id')
    user_email = perform.get('user_email')

    if not user_email:
        print(f'{user_id}의 이메일이 없습니다!')
        continue

    for performance in perform.get('performances',[]):
        open_date = performance.get('open_date')
        if open_date and tomorrow_str in open_date:
            open_date = performance.get('open_date')
            poster_url = performance.get('poster_url')
            location = performance.get('location')
            title = performance.get('title')

            email_subject = f'🔔"{title}" 오픈 알림🔔'
            email_body = f"""
            안녕하세요 {user_id}님!<br><br>

            <strong>"{title}"</strong>의 티켓이 내일 오픈합니다.<br>
            <br>
            <strong>티켓 오픈</strong> : {open_date}<br>
            <strong>공연 이름</strong> : {title}<br>
            <strong>공연 장소</strong> : {location}<br>
            <br>
            <img src="{poster_url}" alt="포스터" style="max-width: 500px;"><br>
            <br>
            감사합니다 !<br>
            <br>
            <strong>Ticket Moa</strong>
            """
            send_email(user_email, email_subject, email_body)   
        


        



    


