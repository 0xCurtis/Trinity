from sqlalchemy import create_engine, Column, Integer, String, DateTime
import datetime
from .base import Base


class LogEntry(Base):
    __tablename__ = 'log_entries'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    level = Column(String)
    message = Column(String)
    source = Column(String)

    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,  # Ensure datetime is converted to string
            'level': self.level,
            'message': self.message,
            'source': self.source
        }
