from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, Request
import jwt

from app.config import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_current_user(request: Request, settings: Annotated[Settings, Depends(get_settings)]):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, settings.SUPABASE_JWT_SECRET_KEY, algorithms=["HS256"], audience="authenticated")
        return {"user_id": payload.get("sub")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
