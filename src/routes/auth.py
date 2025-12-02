from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from .. import schemas
from ..deps import get_db, get_current_user, get_client_ip
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
from .. import sessions as session_mgmt
from ..logging_config import log_login, log_2fa_verify, log_logout, log_password_change

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=schemas.LoginResponse)
def login(body: schemas.LoginRequest, request: Request, db: Session = Depends(get_db), response: Response = Response()):
    ip_address = get_client_ip(request)
    user: User | None = db.query(User).filter(User.email == body.email).first()  # type: ignore[attr-defined]

    if not user or not verify_password(body.password, user.password_hash):  # type: ignore[attr-defined]
        log_login(body.email, success=False, ip_address=ip_address, reason="invalid_credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.active:  # type: ignore[attr-defined]
        log_login(body.email, success=False, ip_address=ip_address, reason="user_inactive")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User inactive",
        )

    # Si el usuario tiene 2FA habilitado, requiere verificación
    if user.totp_enabled:  # type: ignore[attr-defined]
        # Crear token temporal para 2FA (JWT)
        session_token = create_session_token(str(user.id))  # type: ignore[attr-defined]
        log_login(body.email, success=True, ip_address=ip_address, reason="requires_2fa")
        return schemas.LoginResponse(needs_2fa=True, session_token=session_token)

    # Sin 2FA, crear sesión y retornar tokens
    log_login(body.email, success=True, ip_address=ip_address)

    # Crear sesión basada en cookies
    session_token = session_mgmt.create_session(
        db,
        user.id,  # type: ignore[attr-defined]
        ip_address=ip_address,
        user_agent=request.headers.get("User-Agent"),
        hours=24
    )

    # Crear tokens JWT (mantener compatibilidad con SPA)
    access = create_access_token(str(user.id))  # type: ignore[attr-defined]
    refresh = create_refresh_token(str(user.id))  # type: ignore[attr-defined]

    # Agregar cookie de sesión
    response.set_cookie(
        "session_token",
        session_token,
        max_age=24 * 3600,  # 24 horas
        httponly=True,
        secure=True,
        samesite="lax"
    )

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


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    """Revoca la sesión actual del usuario"""
    session_token = request.cookies.get("session_token")
    ip_address = get_client_ip(request)

    if session_token:
        session_mgmt.revoke_session(db, session_token)

    # Log logout
    # Intentar obtener user_id de la sesión (antes de revocarla)
    from ..deps import get_current_user_optional
    user = get_current_user_optional(request, db)
    if user:
        log_logout(user.id, user.email, ip_address=ip_address)  # type: ignore[attr-defined, arg-type]

    response = Response(content='{"ok": true}', media_type="application/json")
    response.delete_cookie("session_token")
    return {"ok": True}


@router.post("/change-password")
def change_password(
    body: schemas.ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    db_user: User | None = db.query(User).filter(User.id == user.id).first()  # type: ignore[attr-defined]
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not db_user.email.endswith("@inacapmail.cl"):  # type: ignore[attr-defined]
        log_password_change(user.id, user.email, success=False, reason="not_inacap_domain")  # type: ignore[attr-type]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo cuentas @inacapmail.cl pueden cambiar contraseña",
        )
    if not verify_password(body.current_password, db_user.password_hash):  # type: ignore[attr-defined]
        log_password_change(user.id, user.email, success=False, reason="incorrect_current_password")  # type: ignore[attr-type]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contraseña actual incorrecta")

    db_user.password_hash = hash_password(body.new_password)  # type: ignore[attr-defined]
    db.commit()
    log_password_change(user.id, user.email, success=True)  # type: ignore[attr-type]
    return {"ok": True}


@router.post("/verify-2fa", response_model=schemas.TokenPair)
def verify_2fa(body: schemas.Verify2FARequest, request: Request, db: Session = Depends(get_db), response: Response = Response()):
    """Verifica código TOTP y retorna tokens de acceso"""
    ip_address = get_client_ip(request)

    # Decodificar session token
    try:
        payload = decode_token(body.session_token, expected_type="session")
        user_id = payload.get("sub")
    except HTTPException:
        log_2fa_verify(user_id=-1, success=False, ip_address=ip_address)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    # Obtener usuario
    user: User | None = db.query(User).filter(User.id == int(user_id)).first()  # type: ignore[attr-defined]
    if not user or not user.totp_enabled:  # type: ignore[attr-defined]
        log_2fa_verify(user_id=int(user_id), success=False, ip_address=ip_address)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session or 2FA not enabled",
        )

    # Verificar código TOTP
    if not verify_totp(user.totp_secret, body.totp_code):  # type: ignore[attr-defined]
        log_2fa_verify(user_id=int(user_id), success=False, ip_address=ip_address)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid TOTP code",
        )

    # 2FA verificado correctamente
    log_2fa_verify(user_id=int(user_id), success=True, ip_address=ip_address)

    # Crear sesión basada en cookies
    session_token = session_mgmt.create_session(
        db,
        int(user_id),  # type: ignore[arg-type]
        ip_address=ip_address,
        user_agent=request.headers.get("User-Agent"),
        hours=24
    )

    # Crear tokens JWT (mantener compatibilidad)
    access = create_access_token(str(user_id))  # type: ignore[arg-type]
    refresh = create_refresh_token(str(user_id))  # type: ignore[arg-type]

    # Agregar cookie de sesión
    response.set_cookie(
        "session_token",
        session_token,
        max_age=24 * 3600,
        httponly=True,
        secure=True,
        samesite="lax"
    )

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
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Permite a un usuario (solo @inacapmail.cl) habilitar su propio 2FA"""
    if not user.email.endswith("@inacapmail.cl"):  # type: ignore[attr-defined]
        from ..logging_config import log_admin_action
        log_admin_action(user.id, "2fa_setup_denied", f"email={user.email}, reason=not_inacap_domain")  # type: ignore[attr-type]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo cuentas @inacapmail.cl pueden habilitar 2FA",
        )
    secret, qr_code = setup_2fa(user.email)  # type: ignore[attr-defined]
    user.totp_secret = secret  # type: ignore[attr-defined]
    user.totp_enabled = True  # type: ignore[attr-defined]
    db.commit()

    from ..logging_config import log_admin_action
    log_admin_action(user.id, "2fa_setup", f"email={user.email}")  # type: ignore[attr-type]

    return schemas.Setup2FAResponse(secret=secret, qr_code=qr_code)
