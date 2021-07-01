from sqlalchemy.orm import declarative_base
Base = declarative_base()
from sqlalchemy import Column, Integer, String, DateTime, Boolean

class TelegramUser(Base):
    __tablename__ = 'telegram_users'
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer)
    user_id = Column(Integer)
    access_hash = Column(String)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    has_photo = Column(Boolean)
    is_bot = Column(Boolean)
    last_seen = Column(String)
    last_online = Column(DateTime)
    is_invited = Column(Boolean)
    invite_result = Column(String)
    invited_date = Column(DateTime)