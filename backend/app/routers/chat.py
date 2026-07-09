from fastapi import APIRouter, HTTPException

from app.schemas import ChatRequest, ChatResponse
from app.agent.graph import run_agent_turn

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    try:
        result = run_agent_turn(payload.message, thread_id=payload.thread_id)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return ChatResponse(reply=result["reply"], tool_calls=result["tool_calls"], thread_id=payload.thread_id)
