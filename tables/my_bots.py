from sqlalchemy.orm import declarative_base
Base = declarative_base()
from sqlalchemy import Column, Integer, String, DateTime, Boolean

class MyBot(Base):
    __tablename__ = 'my_bots'
    id = Column(Integer, primary_key=True)
    phone = Column(String)
    api_id = Column(String)
    api_hash = Column(String)
    note = Column(String)
    last_used = Column(DateTime)
    is_used = Column(Boolean)
    is_paused = Column(Boolean)
    paused_date = Column(DateTime)
