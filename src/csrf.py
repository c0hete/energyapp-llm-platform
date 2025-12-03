import secrets
from fastapi import HTTPException, status, Request


def generate_csrf_token() -> str:
    """Generate a random CSRF token"""
    return secrets.token_urlsafe(32)


def validate_csrf_token(request: Request, token_from_request: str) -> bool:
    """
    Validate CSRF token from request
    Expects the CSRF token to be sent in X-CSRF-Token header
    """
    if request.method in ["GET", "HEAD", "OPTIONS"]:
        # Safe methods don't need CSRF protection
        return True

    # For POST, PUT, DELETE requests, validate the token
    csrf_token_from_header = request.headers.get("X-CSRF-Token")
    csrf_token_from_cookie = request.cookies.get("csrf_token")

    # The token from the request (header) must match the cookie
    if not csrf_token_from_header or not csrf_token_from_cookie:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing"
        )

    if csrf_token_from_header != csrf_token_from_cookie:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token"
        )

    return True
