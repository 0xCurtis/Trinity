from sqlalchemy import Column, Integer, String, DateTime, Boolean
import datetime
from .base import Base

class PipelineInfos(Base):
    __tablename__ = 'pipelines'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_run = Column(DateTime, default=datetime.datetime.utcnow)
    enabled = Column(Boolean, default=True)
    source = Column(String, nullable=False)
    middleware = Column(String, nullable=False)
    post = Column(String, nullable=False)
    trigger = Column(String, nullable=False)
    next_run = Column(DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'last_run': self.last_run,
            'enabled': self.enabled,
            'source': self.source,
            'middleware': self.middleware,
            'post': self.post,
            'trigger': self.trigger,
            'next_run': self.next_run
        }


if __name__ == "__main__":
    pass