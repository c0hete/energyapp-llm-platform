from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from .. import schemas
from ..deps import get_db, get_current_user
from ..models import User
from ..auth import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=schemas.TokenPair)
def login(body: schemas.LoginRequest, db: Session = Depends(get_db)):
    user: User | None = db.query(User).filter(User.email == body.email).first()  # type: ignore[attr-defined]
    if not user or not verify_password(body.password, user.password_hash):  # type: ignore[attr-defined]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.active:  # type: ignore[attr-defined]
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User inactive",
        )
    access = create_access_token(str(user.id))  # type: ignore[attr-defined]
    refresh = create_refresh_token(str(user.id))  # type: ignore[attr-defined]
    return schemas.TokenPair(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=schemas.TokenPair)
def refresh_token(request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth.split()[1]
    payload = decode_token(token, expected_type="refresh")
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == int(user_id)).first()  # type: ignore[attr-defined]
    if not user or not user.active:  # type: ignore[attr-defined]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access = create_access_token(str(user.id))  # type: ignore[attr-defined]
    refresh = create_refresh_token(str(user.id))  # type: ignore[attr-defined]
    return schemas.TokenPair(access_token=access, refresh_token=refresh)


@router.get("/me", response_model=schemas.UserBase)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/change-password")
def change_password(
    body: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    db_user: User | None = db.query(User).filter(User.id == user.id).first()  # type: ignore[attr-defined]
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not verify_password(body.current_password, db_user.password_hash):  # type: ignore[attr-defined]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contraseña actual incorrecta")
    db_user.password_hash = hash_password(body.new_password)  # type: ignore[attr-defined]
    db.commit()
    return {"ok": True}
