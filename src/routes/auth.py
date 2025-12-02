from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from .. import schemas
from ..deps import get_db, get_current_user
from ..models import User
from ..auth import (
    verify_password,
    create_access_token,
    create_refresh_token,
    create_session_token,
    decode_token,
    hash_password,
)
from ..totp import verify_totp, setup_2fa

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=schemas.LoginResponse)
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

    # Si el usuario tiene 2FA habilitado, requiere verificación
    if user.totp_enabled:  # type: ignore[attr-defined]
        session_token = create_session_token(str(user.id))  # type: ignore[attr-defined]
        return schemas.LoginResponse(needs_2fa=True, session_token=session_token)

    # Sin 2FA, retorna tokens directamente
    access = create_access_token(str(user.id))  # type: ignore[attr-defined]
    refresh = create_refresh_token(str(user.id))  # type: ignore[attr-defined]
    return schemas.LoginResponse(
        needs_2fa=False, access_token=access, refresh_token=refresh
    )


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


@router.get("/demo-qr-codes", response_model=schemas.DemoQRCodesResponse)
def get_demo_qr_codes(db: Session = Depends(get_db)):
    """Obtiene los QR codes de los usuarios demo para mostrar en el login"""
    from ..totp import get_totp_provisioning_uri, generate_qr_code_base64

    # Emails de usuarios demo
    demo_emails = [
        "administrador@alvaradomazzei.cl",
        "trabajador@alvaradomazzei.cl",
        "supervisor@alvaradomazzei.cl",
    ]

    demo_qrs = []
    for email in demo_emails:
        user = db.query(User).filter(User.email == email).first()  # type: ignore[attr-defined]
        if user and user.totp_enabled and user.totp_secret:  # type: ignore[attr-defined]
            uri = get_totp_provisioning_uri(user.totp_secret, email)  # type: ignore[attr-defined]
            qr_code = generate_qr_code_base64(uri)
            demo_qrs.append(
                schemas.DemoQRCode(
                    email=email,
                    role=user.role,  # type: ignore[attr-defined]
                    qr_code=qr_code,
                    secret=user.totp_secret,  # type: ignore[attr-defined]
                )
            )

    return schemas.DemoQRCodesResponse(demo_qrs=demo_qrs)


@router.post("/change-password")
def change_password(
    body: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    db_user: User | None = db.query(User).filter(User.id == user.id).first()  # type: ignore[attr-defined]
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not db_user.email.endswith("@inacapmail.cl"):  # type: ignore[attr-defined]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo cuentas @inacapmail.cl pueden cambiar contraseña",
        )
    if not verify_password(body.current_password, db_user.password_hash):  # type: ignore[attr-defined]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contraseña actual incorrecta")
    db_user.password_hash = hash_password(body.new_password)  # type: ignore[attr-defined]
    db.commit()
    return {"ok": True}


@router.post("/verify-2fa", response_model=schemas.TokenPair)
def verify_2fa(body: schemas.Verify2FARequest, db: Session = Depends(get_db)):
    """Verifica código TOTP y retorna tokens de acceso"""
    # Decodificar session token
    try:
        payload = decode_token(body.session_token, expected_type="session")
        user_id = payload.get("sub")
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    # Obtener usuario
    user: User | None = db.query(User).filter(User.id == int(user_id)).first()  # type: ignore[attr-defined]
    if not user or not user.totp_enabled:  # type: ignore[attr-defined]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session or 2FA not enabled",
        )

    # Verificar código TOTP
    if not verify_totp(user.totp_secret, body.totp_code):  # type: ignore[attr-defined]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid TOTP code",
        )

    # Códigos validos, retornar tokens
    access = create_access_token(str(user.id))  # type: ignore[attr-defined]
    refresh = create_refresh_token(str(user.id))  # type: ignore[attr-defined]
    return schemas.TokenPair(access_token=access, refresh_token=refresh)


@router.post("/register")
def register(body: schemas.RegisterRequest, db: Session = Depends(get_db)):
    """Registra un nuevo usuario con dominio permitido"""
    # Validar dominio permitido
    allowed_domains = ["@alvaradomazzei.cl", "@inacapmail.cl"]
    if not any(body.email.endswith(domain) for domain in allowed_domains):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten correos @alvaradomazzei.cl o @inacapmail.cl",
        )

    # Verificar si el usuario ya existe
    existing_user = db.query(User).filter(User.email == body.email).first()  # type: ignore[attr-defined]
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo ya esta registrado",
        )

    # Crear nuevo usuario
    try:
        new_user = User(
            email=body.email,
            password_hash=hash_password(body.password),
            role="user",
            active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"ok": True, "message": "Usuario creado exitosamente", "user_id": new_user.id}  # type: ignore[attr-defined]
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear usuario",
        )


@router.post("/setup-2fa", response_model=schemas.Setup2FAResponse)
def setup_2fa_endpoint(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Permite a un usuario (solo @inacapmail.cl) habilitar su propio 2FA"""
    if not user.email.endswith("@inacapmail.cl"):  # type: ignore[attr-defined]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo cuentas @inacapmail.cl pueden habilitar 2FA",
        )
    secret, qr_code = setup_2fa(user.email)  # type: ignore[attr-defined]
    user.totp_secret = secret  # type: ignore[attr-defined]
    user.totp_enabled = True  # type: ignore[attr-defined]
    db.commit()
    return schemas.Setup2FAResponse(secret=secret, qr_code=qr_code)


@router.post("/setup-2fa", response_model=schemas.Setup2FAResponse)
def setup_2fa_endpoint(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Permite a un usuario (solo @inacapmail.cl) habilitar su propio 2FA"""
    if not user.email.endswith("@inacapmail.cl"):  # type: ignore[attr-defined]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo cuentas @inacapmail.cl pueden habilitar 2FA",
        )
    secret, qr_code = setup_2fa(user.email)  # type: ignore[attr-defined]
    user.totp_secret = secret  # type: ignore[attr-defined]
    user.totp_enabled = True  # type: ignore[attr-defined]
    db.commit()
    return schemas.Setup2FAResponse(secret=secret, qr_code=qr_code)
