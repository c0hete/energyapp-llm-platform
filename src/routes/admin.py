from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from .. import schemas
from ..deps import get_db, require_admin_or_supervisor
from ..models import User, Conversation, Message

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[schemas.AdminUser])
def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_or_supervisor),
):
    q = db.query(User)  # type: ignore[attr-defined]
    if getattr(admin, "role", "") == "supervisor":
        q = q.filter((User.role == "trabajador") | (User.id == admin.id))  # type: ignore[attr-defined]
    users = (
        q.order_by(User.created_at.desc())  # type: ignore[attr-defined]
        .limit(limit)
        .offset(offset)
        .all()
    )

    user_ids = [u.id for u in users]  # type: ignore[attr-defined]
    last_map: dict[int, datetime | None] = {uid: None for uid in user_ids}
    if user_ids:
        rows = (
            db.query(Conversation.user_id, func.max(Message.created_at))  # type: ignore[attr-defined]
            .join(Message, Message.conversation_id == Conversation.id)  # type: ignore[attr-defined]
            .filter(Conversation.user_id.in_(user_ids))  # type: ignore[attr-defined]
            .group_by(Conversation.user_id)
            .all()
        )
        for uid, last_dt in rows:
            last_map[uid] = last_dt

    result: list[schemas.AdminUser] = []
    for u in users:
        result.append(
            schemas.AdminUser(
                id=u.id,  # type: ignore[attr-defined]
                email=u.email,  # type: ignore[attr-defined]
                role=u.role,  # type: ignore[attr-defined]
                active=u.active,  # type: ignore[attr-defined]
                created_at=u.created_at,  # type: ignore[attr-defined]
                last_activity=last_map.get(u.id),  # type: ignore[attr-defined]
            )
        )
    return result


@router.patch("/users/{user_id}", response_model=schemas.UserBase)
def update_user(user_id: int, active: bool | None = None, role: str | None = None, db: Session = Depends(get_db), admin: User = Depends(require_admin_or_supervisor)):
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
    user_id: int | None = Query(None, ge=1),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_or_supervisor),
):
    q = db.query(Conversation).join(User, User.id == Conversation.user_id)  # type: ignore[attr-defined]
    if getattr(admin, "role", "") == "supervisor":
        q = q.filter((User.role == "trabajador") | (User.id == admin.id))  # type: ignore[attr-defined]
    if user_id:
        q = q.filter(Conversation.user_id == user_id)  # type: ignore[attr-defined]
    convs = q.order_by(Conversation.created_at.desc()).limit(limit).offset(offset).all()
    return convs


@router.get("/conversations/{conversation_id}/messages", response_model=list[schemas.MessageBase])
def list_conv_messages(
    conversation_id: int,
    limit: int = Query(100, ge=1, le=400),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_or_supervisor),
):
    conv = (
        db.query(Conversation)
        .join(User, User.id == Conversation.user_id)  # type: ignore[attr-defined]
        .filter(Conversation.id == conversation_id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if getattr(admin, "role", "") == "supervisor":
        owner = getattr(conv, "user", None)
        if not owner or (owner.role not in ("trabajador",) and owner.id != admin.id):  # type: ignore[attr-defined]
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    msgs = (
        db.query(Message)  # type: ignore[attr-defined]
        .filter(Message.conversation_id == conversation_id)  # type: ignore[attr-defined]
        .order_by(Message.created_at.asc())  # type: ignore[attr-defined]
        .limit(limit)
        .offset(offset)
        .all()
    )
    return msgs


@router.post("/conversations/{conversation_id}/reassign", response_model=schemas.ConversationBase)
def reassign_conversation(
    conversation_id: int,
    body: schemas.ReassignConversationRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_or_supervisor),
):
    conv = (
        db.query(Conversation)
        .join(User, User.id == Conversation.user_id)  # type: ignore[attr-defined]
        .filter(Conversation.id == conversation_id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if getattr(admin, "role", "") == "supervisor":
        owner = getattr(conv, "user", None)
        if not owner or (owner.role not in ("trabajador",) and owner.id != admin.id):  # type: ignore[attr-defined]
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    target = None
    if body.target_user_id:
        target = db.query(User).filter(User.id == body.target_user_id, User.active.is_(True)).first()  # type: ignore[attr-defined]
    elif body.target_email:
        target = db.query(User).filter(User.email == body.target_email, User.active.is_(True)).first()  # type: ignore[attr-defined]
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found or inactive")

    prev_user_id = conv.user_id  # type: ignore[attr-defined]
    conv.user_id = target.id  # type: ignore[attr-defined]
    conv.updated_at = datetime.utcnow()  # type: ignore[attr-defined]

    note = Message(  # type: ignore[attr-defined]
        conversation_id=conv.id,  # type: ignore[attr-defined]
        role="system",
        content=f"Conversacion reasignada de user_id={prev_user_id} a user_id={target.id} por admin_id={admin.id}",
    )
    db.add(note)
    db.commit()
    db.refresh(conv)
    return conv
