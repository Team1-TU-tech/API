import os
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# MongoDB 연결
load_dotenv()
mongo_uri = 'mongodb+srv://hahahello777:VIiYTK9NobgeM1hk@cluster0.5vlv3.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0'
client = MongoClient(mongo_uri)
print(mongo_uri)
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

#print(performs)

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
    for performance in perform.get('performances',[]):
        open_date = performance.get('open_date')
        if tomorrow_str in open_date:
            perform_id = performance.get('id', None)
            user_id = performance.get('user_id', None)
            user_email = performance.get('user_email', None)

        #title = perform['title']
        #start_date = perform['start_date']
        #end_date = perform['end_date']
        #location = perform['location']
        #open_date = perform['open_date']

            if user_email:
                email_subject = f"🔔{perform_id} 오픈 알림🔔"
                email_body = f"""
                안녕하세요 {user_id}님! 

                {perform_id}의 티켓이 내일 오픈합니다. 

                오픈 날짜: {open_date}

                감사합니다 !
                Ticket Moa
                """
                send_email(user_email, email_subject, email_body)
           
            else:
                #print(f"{perform.get('title')}의 open_date가 없습니다")
                print('메세지 전송 실패')


        



    



