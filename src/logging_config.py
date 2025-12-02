"""
Configuración centralizada de logging especializado
Loggers: auth.log, audit.log, app.log
"""
import logging
import logging.handlers
from pathlib import Path
from .config import get_settings

# Crear directorio de logs
Path("./logs").mkdir(parents=True, exist_ok=True)

# Configuración de settings
settings = get_settings()

# Formato de logs
DETAILED_FORMAT = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

AUTH_FORMAT = logging.Formatter(
    "%(asctime)s [%(eventType)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def get_auth_logger():
    """Logger de autenticación: login, logout, 2FA, sesiones"""
    logger = logging.getLogger("energyapp.auth")

    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    # Handler para archivo
    handler = logging.handlers.RotatingFileHandler(
        "./logs/auth.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=7
    )
    handler.setFormatter(AUTH_FORMAT)
    logger.addHandler(handler)

    # Handler para consola (opcional)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(AUTH_FORMAT)
    logger.addHandler(console_handler)

    return logger


def get_audit_logger():
    """Logger de auditoría: cambios de roles, reasignaciones, cambio password"""
    logger = logging.getLogger("energyapp.audit")

    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.handlers.RotatingFileHandler(
        "./logs/audit.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=7
    )
    handler.setFormatter(AUTH_FORMAT)
    logger.addHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(AUTH_FORMAT)
    logger.addHandler(console_handler)

    return logger


def get_app_logger():
    """Logger de aplicación: errores, warnings, info general"""
    logger = logging.getLogger("energyapp.app")

    if logger.hasHandlers():
        return logger

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Handler para archivo
    handler = logging.handlers.RotatingFileHandler(
        "./logs/app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=7
    )
    handler.setFormatter(DETAILED_FORMAT)
    logger.addHandler(handler)

    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(DETAILED_FORMAT)
    logger.addHandler(console_handler)

    return logger


# Funciones auxiliares para logging
def log_session_create(user_id: int, email: str, ip_address: str | None = None):
    """Log: nueva sesión creada"""
    logger = get_auth_logger()
    logger.info(
        f"SESSION_CREATE | user_id={user_id}, email={email}, ip={ip_address or 'unknown'}",
        extra={"eventType": "SESSION_CREATE"}
    )


def log_session_validate(user_id: int, ip_address: str | None = None, success: bool = True):
    """Log: sesión validada"""
    logger = get_auth_logger()
    status = "success" if success else "failed"
    logger.info(
        f"SESSION_VALIDATE | user_id={user_id}, ip={ip_address or 'unknown'}, status={status}",
        extra={"eventType": "SESSION_VALIDATE"}
    )


def log_login(email: str, success: bool, ip_address: str | None = None, reason: str = ""):
    """Log: intento de login"""
    logger = get_auth_logger()
    status = "success" if success else "failed"
    msg = f"LOGIN | email={email}, status={status}, ip={ip_address or 'unknown'}"
    if reason:
        msg += f", reason={reason}"
    logger.info(msg, extra={"eventType": "LOGIN"})


def log_2fa_verify(user_id: int, success: bool, ip_address: str | None = None):
    """Log: verificación de 2FA"""
    logger = get_auth_logger()
    status = "success" if success else "failed"
    logger.info(
        f"2FA_VERIFY | user_id={user_id}, status={status}, ip={ip_address or 'unknown'}",
        extra={"eventType": "2FA_VERIFY"}
    )


def log_logout(user_id: int, email: str, ip_address: str | None = None):
    """Log: logout"""
    logger = get_auth_logger()
    logger.info(
        f"LOGOUT | user_id={user_id}, email={email}, ip={ip_address or 'unknown'}",
        extra={"eventType": "LOGOUT"}
    )


def log_admin_action(admin_id: int, action: str, details: str):
    """Log: acción de admin"""
    logger = get_audit_logger()
    logger.info(
        f"ADMIN_{action.upper()} | admin_id={admin_id}, {details}",
        extra={"eventType": f"ADMIN_{action.upper()}"}
    )


def log_password_change(user_id: int, email: str, success: bool, reason: str = ""):
    """Log: cambio de contraseña"""
    logger = get_audit_logger()
    status = "success" if success else "failed"
    msg = f"PASSWORD_CHANGE | user_id={user_id}, email={email}, status={status}"
    if reason:
        msg += f", reason={reason}"
    logger.info(msg, extra={"eventType": "PASSWORD_CHANGE"})


def log_error(error_type: str, user_id: int | None = None, details: str = ""):
    """Log: error de autenticación/seguridad"""
    logger = get_app_logger()
    msg = f"ERROR_{error_type}"
    if user_id:
        msg += f" | user_id={user_id}"
    if details:
        msg += f", {details}"
    logger.error(msg)
