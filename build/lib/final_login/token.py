from jose import jwt 
from datetime import datetime, timedelta
from typing import Dict
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def create_access_token(data: Dict[str, str], expires_delta: timedelta, SECRET_KEY, algorithm=ALGORITHM) -> str:
    """ Access Token 생성 """
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: Dict[str, str], expires_delta: timedelta) -> str:
    """ Refresh Token 생성 """
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


