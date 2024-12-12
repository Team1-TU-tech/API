from typing import List, Optional
from pydantic import BaseModel, root_validator
from contextlib import asynccontextmanager

def get_database():

    class Artist(BaseModel):
        artist_name: str
        artist_url: str

    class Casting(BaseModel):
        role: str
        actor: str

    class Price(BaseModel):
        seat: str
        amount: str

    class Shows(BaseModel):
        title: str
        category: str
        location: str
        region: str
        price: List[Price]
        start_date: str
        end_date: str
        show_time: str
        running_time: str
        casting: List[Casting]
        rating: str
        description: str
        poster_url: str
        open_date: str
        pre_open_date: str
        artist: List[Artist]
        hosts: dict

    @root_validator(pre=True)
    def set_casting_default(cls, values):
        if 'casting' not in values or values['casting'] is None:
            values['casting'] = []  # casting 필드가 None일 경우 빈 리스트로 설정
        if 'artist' not in values or values['artist'] is None:
            values['artist'] = []
        if 'price' not in values or values['price'] is None:
            values['price'] = []

    return Artist, Casting, Price, Shows