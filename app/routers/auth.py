from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
import jwt

from app.config import Settings
from app.dependencies import get_settings

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)


@router.post("/login")
async def login(response: Response, token: dict, settings: Annotated[Settings, Depends(get_settings)]):
    jwt_token = token.get("token")
    if not jwt_token:
        raise HTTPException(status_code=400, detail="Missing token")
    
    try:
        # Need to set audience="authenticated" for PyJWT to properly decode Supabase JWT
        payload = jwt.decode(jwt_token, settings.SUPABASE_JWT_SECRET_KEY, algorithms=["HS256"], audience="authenticated")
        user_id = payload.get("sub")

        # Set HttpOnly cookie
        response.set_cookie(
            key="access_token",
            value=jwt_token,
            httponly=True,
            secure=True,  # Requires HTTPS in production
            samesite="Lax"
        )

        return {"message": "Authenticated", "user_id": user_id}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
