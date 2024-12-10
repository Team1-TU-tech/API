from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_PASSWORD = os.getenv("MONGOPASS", "VIiYTK9NobgeM1hk")
MONGO_URL = f"mongodb+srv://hahahello777:{MONGO_PASSWORD}@cluster0.5vlv3.mongodb.net/test?retryWrites=true&w=majority&appName=Cluster0"

client = AsyncIOMotorClient(MONGO_URL)
db = client.get_database("signup")
user_collection = db.get_collection("users")

