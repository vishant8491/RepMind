from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

SENTIMENTS = ("Positive", "Neutral", "Negative")
INTERACTION_TYPES = ("Meeting", "Call", "Email", "Conference", "Other")


class InteractionBase(BaseModel):
    hcp_name: str = Field(..., min_length=1, max_length=200)
    interaction_type: str = Field(default="Meeting")
    interaction_date: date
    interaction_time: Optional[str] = None
    attendees: List[str] = Field(default_factory=list)
    topics_discussed: Optional[str] = None
    materials_shared: List[str] = Field(default_factory=list)
    samples_distributed: List[str] = Field(default_factory=list)
    sentiment: str = Field(default="Neutral")
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    """All fields optional — only the ones sent are updated."""

    hcp_name: Optional[str] = None
    interaction_type: Optional[str] = None
    interaction_date: Optional[date] = None
    interaction_time: Optional[str] = None
    attendees: Optional[List[str]] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[List[str]] = None
    samples_distributed: Optional[List[str]] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None


class InteractionOut(InteractionBase):
    id: int
    source: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    tool_calls: List[dict] = Field(default_factory=list)
    thread_id: str
