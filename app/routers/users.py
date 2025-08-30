import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.dependencies import get_supabase

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
)

logger = logging.getLogger(__name__)


@router.delete("/{user_id}")
async def delete_user(user_id: str) -> JSONResponse:
    """
    Deletes a user and all their associated data, including:
    - All chatrooms owned by the user
    - All documents uploaded in those chatrooms
    - All messages in those chatrooms (handled by cascading deletes)
    - All invites to those chatrooms (handled by cascading deletes)
    - The user entry in the Supabase public.users table
    - The user entry in Supabase auth.users table

    Args:
        user_id (str): The ID of the user to delete.
 
    Returns:
        JSONResponse: A response indicating success or failure of the deletion.
    """
    supabase = get_supabase()

    try:
        logger.info(f"DELETE - {router.prefix}/users\nReceived request to delete user {user_id}")

        # Delete all document files from bucket in all chatrooms owned by the user
        documents_response = (
            supabase.rpc("get_documents_in_chatrooms_owned_by_user", {"p_user_id": user_id})
            .execute()
        )

        documents_paths = [
            f"{doc['chatroom_id']}/{doc['document_id']}" for doc in documents_response.data
        ] + [
            f"{doc['chatroom_id']}" for doc in documents_response.data
        ]
        (
            supabase.storage
            .from_("knowledge-bases")
            .remove(documents_paths)
        )

        # Delete all attachment files from bucket in all chatrooms owned by the user
        attachments_response = (
            supabase.rpc("get_attachments_in_chatrooms_owned_by_user", {"p_user_id": user_id})
            .execute()
        )
        attachments_paths = [
            f"{att['chatroom_id']}/{att['filename']}" for att in attachments_response.data
        ] + [
            f"{att['chatroom_id']}" for att in attachments_response.data
        ]
        (
            supabase.storage
            .from_("attachments")
            .remove(attachments_paths)
        )

        # Delete all chatrooms owned by the user
        (
            supabase.table("chatrooms")
            .delete()
            .eq("creator_id", user_id)
            .execute()
        )

        # Delete user from Supabase public.users table
        delete_user_response = (
            supabase.table("users")
            .delete()
            .eq("user_id", user_id)
            .execute()
        )

        # Delete user from Supabase using supabase.auth.admin.delete_user()
        auth_id = delete_user_response.data[0].get("auth_id")
        supabase.auth.admin.delete_user(auth_id)

        logger.info(f"DELETE - {router.prefix}/users\nSuccessfully deleted user {user_id}.")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Successfully deleted user."},
        )
    except Exception as e:
        logger.exception(f"Error deleting user {user_id}: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"Failed to delete user {user_id}: {str(e)}"},
        )
