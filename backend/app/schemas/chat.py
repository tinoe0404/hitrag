from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[int] = None

class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    status: str
    answer: str
    citations: List[Dict[str, Any]]
