from sqlalchemy import Column, Integer, String, DateTime
import datetime
from .base import Base

class PipelineInfos(Base):
    __tablename__ = 'pipelines'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_run = Column(DateTime, default=datetime.datetime.utcnow)
    enabled = Column(Integer, default=1)
    source = Column(String, nullable=False)
    middleware = Column(String, nullable=False)
    post = Column(String, nullable=False)
    trigger = Column(String, nullable=False)
    next_run = Column(DateTime, default=datetime.datetime.utcnow)

if __name__ == "__main__":
    pass