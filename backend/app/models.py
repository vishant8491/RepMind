from datetime import datetime, date as date_type
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, JSON
from app.database import Base


class Interaction(Base):

    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    hcp_name = Column(String(200), nullable=False, index=True)
    interaction_type = Column(String(50), nullable=False, default="Meeting")
    interaction_date = Column(Date, nullable=False, default=date_type.today)
    interaction_time = Column(String(10), nullable=True)  # stored as "HH:MM"

    attendees = Column(JSON, nullable=True, default=list)
    topics_discussed = Column(Text, nullable=True)
    materials_shared = Column(JSON, nullable=True, default=list)
    samples_distributed = Column(JSON, nullable=True, default=list)

    sentiment = Column(String(20), nullable=False, default="Neutral")
    outcomes = Column(Text, nullable=True)
    follow_up_actions = Column(Text, nullable=True)

    source = Column(String(10), nullable=False, default="form")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "hcp_name": self.hcp_name,
            "interaction_type": self.interaction_type,
            "interaction_date": self.interaction_date.isoformat() if self.interaction_date else None,
            "interaction_time": self.interaction_time,
            "attendees": self.attendees or [],
            "topics_discussed": self.topics_discussed,
            "materials_shared": self.materials_shared or [],
            "samples_distributed": self.samples_distributed or [],
            "sentiment": self.sentiment,
            "outcomes": self.outcomes,
            "follow_up_actions": self.follow_up_actions,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
