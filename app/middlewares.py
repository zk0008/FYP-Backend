from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
import jwt

from app.dependencies import get_settings


async def auth_middleware(request: Request, call_next) -> Response:
    """
    Authenticates the request based on the JWT supplied in the header.

    Args:
        request (Request): The request sent by the client.
    """
    # Allow unauthenticated access to the root path
    if request.url.path == "/":
        return await call_next(request)

    auth_header = request.headers.get("Authorization", None)
    if not auth_header:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Missing Authorization header in request"}
        )
    
    if not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid Authorization header format"}
        )

    try:
        settings = get_settings()
        token = auth_header.split(' ')[1]
        jwt.decode(token, settings.SUPABASE_JWT_SECRET_KEY, algorithms=['HS256'], audience='authenticated')     # Local token validation
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Token expired"}
        )
    except jwt.InvalidTokenError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Invalid token"}
        )

    response = await call_next(request)
    return response
