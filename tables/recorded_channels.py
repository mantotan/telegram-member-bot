from sqlalchemy.orm import declarative_base
Base = declarative_base()
from sqlalchemy import Column, Integer, String, DateTime, Boolean

class RecordedChannel(Base):
    __tablename__ = 'recorded_channels'
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer)
    title = Column(String)
    date = Column(DateTime)
    version = Column(Integer)
    access_hash = Column(String)
    is_megagroup = Column(Boolean)
    is_inviting = Column(Boolean)