from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from passlib.context import CryptContext
from .. import schemas
from ..deps import get_db, require_admin_or_supervisor, require_admin_or_supervisor_hybrid, get_client_ip
from ..models import User, Conversation, Message, UserCreationLog
from ..audit import AuditLogger, AuditAction

router = APIRouter(prefix="/admin", tags=["admin"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/users", response_model=list[schemas.AdminUser])
def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_or_supervisor_hybrid),
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


@router.post("/users", response_model=schemas.UserBase, status_code=status.HTTP_201_CREATED)
def create_user(
    request: Request,
    user_data: schemas.RegisterRequest,
    role: str = Query("usuario", pattern="^(usuario|admin|supervisor|trabajador)$"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_or_supervisor)
):
    """Create a new user (admin only)"""
    ip_address = get_client_ip(request)

    # Check if email already exists
    existing = db.query(User).filter(User.email == user_data.email).first()  # type: ignore[attr-defined]
    if existing:
        AuditLogger.log_user_action(
            db=db,
            action=AuditAction.USER_CREATED,
            admin=admin,
            target_user_id=existing.id,  # type: ignore[attr-defined]
            ip_address=ip_address,
            metadata={"error": "Email already registered", "email": user_data.email}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = pwd_context.hash(user_data.password)
    new_user = User(  # type: ignore[attr-defined]
        email=user_data.email,
        hashed_password=hashed_password,
        role=role,
        active=True
    )
    db.add(new_user)
    db.flush()  # Get user ID without committing

    # Create creation log
    creation_log = UserCreationLog(  # type: ignore[attr-defined]
        user_id=new_user.id,  # type: ignore[attr-defined]
        created_by_admin_id=admin.id,  # type: ignore[attr-defined]
        reason=user_data.reason,
        ip_address=ip_address
    )
    db.add(creation_log)
    db.commit()
    db.refresh(new_user)

    # Audit log
    AuditLogger.log_user_action(
        db=db,
        action=AuditAction.USER_CREATED,
        admin=admin,
        target_user_id=new_user.id,  # type: ignore[attr-defined]
        ip_address=ip_address,
        metadata={"email": new_user.email, "role": role, "reason": user_data.reason}  # type: ignore[attr-defined]
    )

    return new_user


@router.patch("/users/{user_id}", response_model=schemas.UserBase)
def update_user(
    user_id: int,
    request: Request,
    active: bool | None = None,
    role: str | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_or_supervisor)
):
    ip_address = get_client_ip(request)
    user = db.query(User).filter(User.id == user_id).first()  # type: ignore[attr-defined]
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Track changes
    changes = {}
    if active is not None and user.active != active:  # type: ignore[attr-defined]
        changes["active"] = {"from": user.active, "to": active}  # type: ignore[attr-defined]
        user.active = active  # type: ignore[attr-defined]
        # Log activation/deactivation separately
        action = AuditAction.USER_ACTIVATED if active else AuditAction.USER_DEACTIVATED
        AuditLogger.log_user_action(
            db=db,
            action=action,
            admin=admin,
            target_user_id=user_id,
            ip_address=ip_address,
            metadata={"email": user.email}  # type: ignore[attr-defined]
        )

    if role is not None and user.role != role:  # type: ignore[attr-defined]
        changes["role"] = {"from": user.role, "to": role}  # type: ignore[attr-defined]
        user.role = role  # type: ignore[attr-defined]
        AuditLogger.log_user_action(
            db=db,
            action=AuditAction.ROLE_CHANGED,
            admin=admin,
            target_user_id=user_id,
            ip_address=ip_address,
            metadata={"email": user.email, "old_role": changes["role"]["from"], "new_role": role}  # type: ignore[attr-defined]
        )

    if changes:
        db.commit()
        db.refresh(user)
        # General update log
        AuditLogger.log_user_action(
            db=db,
            action=AuditAction.USER_UPDATED,
            admin=admin,
            target_user_id=user_id,
            ip_address=ip_address,
            metadata={"email": user.email, "changes": changes}  # type: ignore[attr-defined]
        )

    return user


@router.get("/conversations", response_model=list[schemas.ConversationBase])
def list_all_conversations(
    user_id: int | None = Query(None, ge=1),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_or_supervisor_hybrid),
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
    admin: User = Depends(require_admin_or_supervisor_hybrid),
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
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_or_supervisor_hybrid),
):
    ip_address = get_client_ip(request)
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

    # Audit log
    AuditLogger.log_conversation_action(
        db=db,
        action=AuditAction.CONVERSATION_REASSIGNED,
        user=admin,
        conversation_id=conversation_id,
        ip_address=ip_address,
        metadata={
            "from_user_id": prev_user_id,
            "to_user_id": target.id,  # type: ignore[attr-defined]
            "to_email": target.email  # type: ignore[attr-defined]
        }
    )

    return conv


@router.get("/audit-logs", response_model=list[schemas.AuditLogResponse])
def get_audit_logs(
    action: str | None = Query(None, description="Filter by action"),
    user_email: str | None = Query(None, description="Filter by user email"),
    status: str | None = Query(None, pattern="^(success|failed|blocked)$"),
    date_from: datetime | None = Query(None, description="Filter from date"),
    date_to: datetime | None = Query(None, description="Filter to date"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin_or_supervisor)
):
    """Get audit logs (admin/supervisor only)"""
    from ..models import AuditLog

    q = db.query(AuditLog)  # type: ignore[attr-defined]

    # Apply filters
    if action:
        q = q.filter(AuditLog.action == action)
    if user_email:
        q = q.filter(AuditLog.user_email.ilike(f"%{user_email}%"))  # type: ignore[attr-defined]
    if status:
        q = q.filter(AuditLog.status == status)
    if date_from:
        q = q.filter(AuditLog.created_at >= date_from)
    if date_to:
        q = q.filter(AuditLog.created_at <= date_to)

    # Order and paginate
    logs = (
        q.order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return logs
