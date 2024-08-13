from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
import datetime
from .base import Base

class MediaHistory(Base):
    __tablename__ = 'media_history'
    id = Column(Integer, primary_key=True)
    media_id = Column(String, nullable=False)  # ID of the media
    pipeline_name = Column(String, nullable=False)  # Name or identifier of the pipeline
    timestamp = Column(DateTime, default=datetime.datetime.utcnow) 

