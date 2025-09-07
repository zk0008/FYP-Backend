from fastapi import HTTPException, Request, Response, status

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
        auth_user_response = supabase.auth.get_user(token)  # JWT validation with Supabase
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.detail if hasattr(e, 'detail') else "Invalid token"
        )

    try:
        user_response = (
            supabase
            .from_("users")
            .select("user_id, username")
            .eq("auth_id", auth_user_response.user.id)
            .execute()
        )

        request.state.user_id = user_response.data[0]["user_id"]
        request.state.username = user_response.data[0]["username"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    response = await call_next(request)
    return response
