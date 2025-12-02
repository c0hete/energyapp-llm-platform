from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from .. import schemas
from ..deps import get_db, get_current_user_hybrid
from ..models import Conversation, Message, User

router = APIRouter(prefix="/conversations", tags=["conversations"])


def generate_title_from_prompt(prompt: str, max_length: int = 50) -> str:
    """Genera un título automático a partir del prompt del usuario."""
    # Tomar las primeras palabras
    words = prompt.strip().split()[:6]
    title = " ".join(words)
    if len(title) > max_length:
        title = title[:max_length-3] + "..."
    return title or "Nueva conversacion"


@router.get("", response_model=list[schemas.ConversationBase])
def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_hybrid),
):
    convs = (
        db.query(Conversation)  # type: ignore[attr-defined]
        .filter(Conversation.user_id == user.id)  # type: ignore[attr-defined]
        .order_by(Conversation.created_at.desc())  # type: ignore[attr-defined]
        .limit(limit)
        .offset(offset)
        .all()
    )
    return convs


@router.post("", response_model=schemas.ConversationBase, status_code=status.HTTP_201_CREATED)
def create_conversation(body: schemas.CreateConversation, db: Session = Depends(get_db), user: User = Depends(get_current_user_hybrid)):
    conv = Conversation(  # type: ignore[attr-defined]
        user_id=user.id,
        title=body.title or "Nueva conversacion",
        status="open",
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@router.post("/{conversation_id}/generate-title")
def generate_title(conversation_id: int, body: schemas.GenerateTitle, db: Session = Depends(get_db), user: User = Depends(get_current_user_hybrid)):
    """Genera automáticamente un título para la conversación basado en el prompt."""
    conv = (
        db.query(Conversation)  # type: ignore[attr-defined]
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)  # type: ignore[attr-defined]
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    title = generate_title_from_prompt(body.prompt)
    conv.title = title  # type: ignore[attr-defined]
    db.commit()
    db.refresh(conv)
    return {"title": title}


@router.get("/{conversation_id}", response_model=schemas.ConversationBase)
def get_conversation(conversation_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user_hybrid)):
    conv = (
        db.query(Conversation)  # type: ignore[attr-defined]
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)  # type: ignore[attr-defined]
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv


@router.patch("/{conversation_id}", response_model=schemas.ConversationBase)
def update_conversation(conversation_id: int, body: schemas.UpdateConversation, db: Session = Depends(get_db), user: User = Depends(get_current_user_hybrid)):
    conv = (
        db.query(Conversation)  # type: ignore[attr-defined]
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)  # type: ignore[attr-defined]
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if body.title is not None:
        conv.title = body.title  # type: ignore[attr-defined]
    if body.status is not None:
        conv.status = body.status  # type: ignore[attr-defined]
    db.commit()
    db.refresh(conv)
    return conv


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user_hybrid)):
    conv = (
        db.query(Conversation)  # type: ignore[attr-defined]
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)  # type: ignore[attr-defined]
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    # Eliminar mensajes primero
    db.query(Message).filter(Message.conversation_id == conversation_id).delete()  # type: ignore[attr-defined]
    db.delete(conv)  # type: ignore[arg-type]
    db.commit()
    return


@router.get("/{conversation_id}/messages", response_model=list[schemas.MessageBase])
def list_messages(
    conversation_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_hybrid),
):
    conv = (
        db.query(Conversation)  # type: ignore[attr-defined]
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)  # type: ignore[attr-defined]
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    msgs = (
        db.query(Message)  # type: ignore[attr-defined]
        .filter(Message.conversation_id == conversation_id)  # type: ignore[attr-defined]
        .order_by(Message.created_at.asc())  # type: ignore[attr-defined]
        .limit(limit)
        .offset(offset)
        .all()
    )
    return msgs
