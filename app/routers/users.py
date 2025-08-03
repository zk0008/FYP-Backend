import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
)

logger = logging.getLogger(__name__)


@router.delete("/{user_id}")
async def delete_user(user_id: str):
    ### The input user_id is the ID of the record in public.users table
    # Delete chatrooms where user is the owner AND contains no other members
    # For chatrooms where user is the owner AND contains other members, transfer ownership to the EARLIEST-JOINED member
    # Delete files from Supabase bucket that belong to the user
    # Delete user from Supabase public.users table
    # Delete user from Supabase using supabase.auth.admin.delete_user()

    pass
