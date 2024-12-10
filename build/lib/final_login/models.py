from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    id: str
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    id: str | None = None

