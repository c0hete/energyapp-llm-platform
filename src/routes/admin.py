from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from .. import schemas
from ..deps import get_db, require_admin
from ..models import User, Conversation, Message

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[schemas.UserBase])
def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    users = (
        db.query(User)  # type: ignore[attr-defined]
        .order_by(User.created_at.desc())  # type: ignore[attr-defined]
        .limit(limit)
        .offset(offset)
        .all()
    )
    return users


@router.patch("/users/{user_id}", response_model=schemas.UserBase)
def update_user(user_id: int, active: bool | None = None, role: str | None = None, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()  # type: ignore[attr-defined]
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if active is not None:
        user.active = active  # type: ignore[attr-defined]
    if role is not None:
        user.role = role  # type: ignore[attr-defined]
    db.commit()
    db.refresh(user)
    return user


@router.get("/conversations", response_model=list[schemas.ConversationBase])
def list_all_conversations(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    convs = (
        db.query(Conversation)  # type: ignore[attr-defined]
        .order_by(Conversation.created_at.desc())  # type: ignore[attr-defined]
        .limit(limit)
        .offset(offset)
        .all()
    )
    return convs


@router.get("/conversations/{conversation_id}/messages", response_model=list[schemas.MessageBase])
def list_conv_messages(
    conversation_id: int,
    limit: int = Query(100, ge=1, le=400),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    msgs = (
        db.query(Message)  # type: ignore[attr-defined]
        .filter(Message.conversation_id == conversation_id)  # type: ignore[attr-defined]
        .order_by(Message.created_at.asc())  # type: ignore[attr-defined]
        .limit(limit)
        .offset(offset)
        .all()
    )
    if msgs is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return msgs
