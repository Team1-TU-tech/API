from pymongo import MongoClient
import os
import certifi

mongopassword = os.getenv("MONGOPASS")
url = f"mongodb+srv://summerham22:{mongopassword}@cluster0.c1zjv.mongodb.net/"
client = MongoClient(url, tlsCAFile=certifi.where())
db = client.TicketMoa

db.Users.insert_one({
                "user_id": user_id,
                "password": password,
                "username": username,
                "email": email,
                "phone_number": phone_number,
                "created_at_timestamp": created_at_timestamp,
                "auth_id": auth_id
            })