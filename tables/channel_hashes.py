from sqlalchemy.orm import declarative_base
Base = declarative_base()
from sqlalchemy import Column, Integer, String

class ChannelHash(Base):
    __tablename__ = 'channel_hashes'
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer)
    bot_api_id = Column(Integer)
    access_hash = Column(String)