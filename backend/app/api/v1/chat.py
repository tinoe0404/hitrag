from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.enums import UserRole
from app.core.deps import get_current_user, get_allowed_tiers
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.conversation import get_user_conversation_or_404
from app.repositories.conversation import (
    create_conversation as create_conversation_repo,
    create_message,
)
from app.rag.retrieval import retrieve
from app.rag.generation import generate_answer, NOT_ENOUGH_INFO_MESSAGE

chat_router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])

@chat_router.post("", response_model=ChatResponse)
def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    allowed_tiers: List[UserRole] = Depends(get_allowed_tiers),
):
    """
    Core RAG chat endpoint:
    - Verifies or creates a conversation enforcing strict ownership boundaries.
    - Persists the incoming question.
    - Runs semantic retrieval using current user access tiers.
    - Invokes grounded answer generation.
    - Persists and returns the assistant's reply.
    """
    # 1. Resolve conversation and verify ownership
    if request.conversation_id is not None:
        conv = get_user_conversation_or_404(db, request.conversation_id, current_user.id)
        conversation_id = conv.id
    else:
        title = request.question.strip()[:40] if request.question.strip() else "New Conversation"
        conv = create_conversation_repo(db, user_id=current_user.id, title=title)
        conversation_id = conv.id

    # 2. Persist user question
    create_message(
        db,
        conversation_id=conversation_id,
        role="user",
        content=request.question,
    )

    # 3. Retrieve context chunks with tier filtering
    # We use top_k=5 as a sensible default
    retrieved = retrieve(db=db, query=request.question, allowed_tiers=allowed_tiers, top_k=5)

    # 4. Generate answer using retrieved chunks
    result = generate_answer(query=request.question, chunks=retrieved)

    # 5. Decide what content to persist for the assistant message
    # For NOT_ENOUGH_INFORMATION: persist the clean user-facing refusal text.
    # For PARSE_ERROR: persist a distinguishable audit message containing [System Parse Error]
    # so we can track and debug parsing failures in telemetry while keeping the user experience clean.
    if result.status == "ANSWERED":
        assistant_content = result.answer
    elif result.status == "NOT_ENOUGH_INFORMATION":
        assistant_content = NOT_ENOUGH_INFO_MESSAGE
    else:  # PARSE_ERROR
        assistant_content = f"[System Parse Error] {NOT_ENOUGH_INFO_MESSAGE}"

    # Persist assistant reply
    assistant_msg = create_message(
        db,
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_content,
    )

    # 6. Return response
    return ChatResponse(
        conversation_id=conversation_id,
        message_id=assistant_msg.id,
        status=result.status,
        answer=result.answer,
        citations=result.citations,
    )
