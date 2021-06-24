from sqlalchemy.orm import declarative_base
Base = declarative_base()
from sqlalchemy import Column, Integer, String, DateTime, Boolean

class ChannelPost(Base):
    __tablename__ = 'channel_posts'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    group_type = Column(String)
    message_type = Column(String)
    posted_date = Column(DateTime)
    message_id = Column(String)
    message = Column(Integer)
    is_posted = Column(Boolean)
    url = Column(String)