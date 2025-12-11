from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from .. import schemas
from ..deps import get_db, get_current_user, get_current_user_from_session, get_client_ip
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
from ..audit import AuditLogger, AuditAction

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(body: schemas.LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip_address = get_client_ip(request)
    user: User | None = db.query(User).filter(User.email == body.email).first()  # type: ignore[attr-defined]

    if not user or not verify_password(body.password, user.password_hash):  # type: ignore[attr-defined]
        AuditLogger.log_auth(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            email=body.email,
            success=False,
            ip_address=ip_address,
            error_message="Invalid credentials"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.active:  # type: ignore[attr-defined]
        AuditLogger.log_auth(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            email=body.email,
            success=False,
            ip_address=ip_address,
            error_message="User inactive",
            user=user
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User inactive",
        )

    # Si el usuario tiene 2FA habilitado, requiere verificación
    if user.totp_enabled:  # type: ignore[attr-defined]
        # Crear token temporal para 2FA (JWT)
        session_token = create_session_token(str(user.id))  # type: ignore[attr-defined]
        AuditLogger.log_auth(
            db=db,
            action=AuditAction.LOGIN_SUCCESS,
            email=body.email,
            success=True,
            ip_address=ip_address,
            user=user
        )
        response_data = {
            "needs_2fa": True,
            "session_token": session_token,
            "access_token": None,
            "refresh_token": None
        }
        return JSONResponse(content=response_data)

    # Sin 2FA, crear sesión y retornar tokens
    AuditLogger.log_auth(
        db=db,
        action=AuditAction.LOGIN_SUCCESS,
        email=body.email,
        success=True,
        ip_address=ip_address,
        user=user
    )

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

    # Crear respuesta JSON con cookies
    response_data = {
        "needs_2fa": False,
        "session_token": session_token,
        "access_token": access,
        "refresh_token": refresh
    }
    response = JSONResponse(content=response_data)
    response.set_cookie(
        "session_token",
        session_token,
        max_age=24 * 3600,  # 24 horas
        httponly=True,
        secure=True,
        samesite="lax"
    )
    return response


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

    # Intentar obtener user antes de revocar la sesión
    from ..deps import get_current_user_optional
    user = get_current_user_optional(request, db)

    if session_token:
        session_mgmt.revoke_session(db, session_token)

    # Log logout
    if user:
        AuditLogger.log_auth(
            db=db,
            action=AuditAction.LOGOUT,
            email=user.email,  # type: ignore[attr-defined]
            success=True,
            ip_address=ip_address,
            user=user
        )

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
    ip_address = get_client_ip(request)
    db_user: User | None = db.query(User).filter(User.id == user.id).first()  # type: ignore[attr-defined]
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not db_user.email.endswith("@inacapmail.cl"):  # type: ignore[attr-defined]
        AuditLogger.log(
            db=db,
            action=AuditAction.PASSWORD_CHANGED,
            user=user,
            status="failed",
            error_message="Not @inacapmail.cl domain",
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo cuentas @inacapmail.cl pueden cambiar contraseña",
        )
    if not verify_password(body.current_password, db_user.password_hash):  # type: ignore[attr-defined]
        AuditLogger.log(
            db=db,
            action=AuditAction.PASSWORD_CHANGED,
            user=user,
            status="failed",
            error_message="Incorrect current password",
            ip_address=ip_address
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contraseña actual incorrecta")

    db_user.password_hash = hash_password(body.new_password)  # type: ignore[attr-defined]
    db.commit()

    AuditLogger.log(
        db=db,
        action=AuditAction.PASSWORD_CHANGED,
        user=user,
        status="success",
        ip_address=ip_address
    )
    return {"ok": True}


@router.post("/verify-2fa")
def verify_2fa(body: schemas.Verify2FARequest, request: Request, db: Session = Depends(get_db)):
    """Verifica código TOTP y retorna tokens de acceso"""
    ip_address = get_client_ip(request)

    # Decodificar session token
    try:
        payload = decode_token(body.session_token, expected_type="session")
        user_id = payload.get("sub")
    except HTTPException:
        AuditLogger.log(
            db=db,
            action="2fa_verify_failed",
            status="failed",
            error_message="Invalid or expired session token",
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    # Obtener usuario
    user: User | None = db.query(User).filter(User.id == int(user_id)).first()  # type: ignore[attr-defined]
    if not user or not user.totp_enabled:  # type: ignore[attr-defined]
        AuditLogger.log(
            db=db,
            action="2fa_verify_failed",
            user_id=int(user_id) if user_id else None,
            status="failed",
            error_message="Invalid session or 2FA not enabled",
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session or 2FA not enabled",
        )

    # Verificar código TOTP
    if not verify_totp(user.totp_secret, body.totp_code):  # type: ignore[attr-defined]
        AuditLogger.log(
            db=db,
            action="2fa_verify_failed",
            user=user,
            status="failed",
            error_message="Invalid TOTP code",
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid TOTP code",
        )

    # 2FA verificado correctamente
    AuditLogger.log(
        db=db,
        action="2fa_verify_success",
        user=user,
        status="success",
        ip_address=ip_address
    )

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

    # Crear respuesta JSON con cookies
    response_data = {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer"
    }
    response = JSONResponse(content=response_data)
    response.set_cookie(
        "session_token",
        session_token,
        max_age=24 * 3600,
        httponly=True,
        secure=True,
        samesite="lax"
    )
    return response


@router.post("/register")
def register(body: schemas.RegisterRequest, request: Request, db: Session = Depends(get_db)):
    """Registra un nuevo usuario con dominio permitido"""
    ip_address = get_client_ip(request)

    # Validar dominio permitido
    allowed_domains = ["@alvaradomazzei.cl", "@inacapmail.cl"]
    if not any(body.email.endswith(domain) for domain in allowed_domains):
        AuditLogger.log(
            db=db,
            action="user_register_failed",
            status="failed",
            error_message="Domain not allowed",
            metadata={"email": body.email},
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se permiten correos @alvaradomazzei.cl o @inacapmail.cl",
        )

    # Verificar si el usuario ya existe
    existing_user = db.query(User).filter(User.email == body.email).first()  # type: ignore[attr-defined]
    if existing_user:
        AuditLogger.log(
            db=db,
            action="user_register_failed",
            status="failed",
            error_message="Email already registered",
            metadata={"email": body.email},
            ip_address=ip_address
        )
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

        AuditLogger.log(
            db=db,
            action=AuditAction.USER_CREATED,
            user=new_user,
            resource_type="user",
            resource_id=new_user.id,  # type: ignore[attr-defined]
            status="success",
            metadata={"self_registered": True},
            ip_address=ip_address
        )

        return {"ok": True, "message": "Usuario creado exitosamente", "user_id": new_user.id}  # type: ignore[attr-defined]
    except Exception as e:
        db.rollback()
        AuditLogger.log(
            db=db,
            action="user_register_failed",
            status="failed",
            error_message=str(e),
            metadata={"email": body.email},
            ip_address=ip_address
        )
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
    ip_address = get_client_ip(request)

    if not user.email.endswith("@inacapmail.cl"):  # type: ignore[attr-defined]
        AuditLogger.log(
            db=db,
            action="2fa_setup_denied",
            user=user,
            status="failed",
            error_message="Not @inacapmail.cl domain",
            ip_address=ip_address
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo cuentas @inacapmail.cl pueden habilitar 2FA",
        )

    secret, qr_code = setup_2fa(user.email)  # type: ignore[attr-defined]
    user.totp_secret = secret  # type: ignore[attr-defined]
    user.totp_enabled = True  # type: ignore[attr-defined]
    db.commit()

    AuditLogger.log(
        db=db,
        action="2fa_setup",
        user=user,
        status="success",
        ip_address=ip_address
    )

    return schemas.Setup2FAResponse(secret=secret, qr_code=qr_code)


@router.get("/me", response_model=schemas.UserBase)
def get_current_user_me(
    user: User = Depends(get_current_user_from_session)
):
    """
    Obtiene datos del usuario autenticado (validación de sesión).
    Usado por Next.js para verificar sesión al cargar.
    """
    return schemas.UserBase(
        id=user.id,  # type: ignore[attr-defined]
        email=user.email,  # type: ignore[attr-defined]
        role=user.role,  # type: ignore[attr-defined]
        active=user.active,  # type: ignore[attr-defined]
        created_at=user.created_at,  # type: ignore[attr-defined]
        updated_at=user.updated_at,  # type: ignore[attr-defined]
    )
