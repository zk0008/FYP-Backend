from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from app.dependencies import get_supabase


async def auth_middleware(request: Request, call_next) -> Response:
    """
    Authenticates the request based on the JWT supplied in the header.

    Args:
        request (Request): The request sent by the client.
    """
    # Allow unauthenticated access to root and documentation endpoints
    ALLOWED_PATHS = {"/", "/docs", "redoc", "/openapi.json"}
    if request.url.path in ALLOWED_PATHS:
        return await call_next(request)

    # Allow unauthenticated access to static files
    if request.url.path.startswith("/static/"):
        return await call_next(request)

    auth_header = request.headers.get("Authorization", None)
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header in request"
        )
    
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format"
        )

    try:
        token = auth_header.split(' ')[1]
        supabase = get_supabase()
        supabase.auth.get_user(token)  # JWT validation with Supabase
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )

    response = await call_next(request)
    return response
