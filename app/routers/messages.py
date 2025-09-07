import logging

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.dependencies import get_supabase

router = APIRouter(
    prefix="/api/messages",
    tags=["messages"],
)

logger = logging.getLogger(__name__)


@router.get("/{chatroom_id}")
async def get_messages(chatroom_id: str):
    """Retrieves all messages for a specific chatroom."""
    try:
        supabase = get_supabase()

        messages_response = supabase.rpc("get_chatroom_messages", {"p_chatroom_id": chatroom_id}).execute()

        if messages_response.data is None:
            messages_response.data = []

        logger.info(f"GET - {router.prefix}/{chatroom_id}\nFound {len(messages_response.data)} message{'s' if len(messages_response.data) != 1 else ''} for chatroom {chatroom_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=messages_response.data
        )
    except Exception as e:
        logger.error(f"GET - {router.prefix}/{chatroom_id}\nError retrieving messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.detail if hasattr(e, 'detail') else str(e)
        )


@router.delete("/{chatroom_id}/{message_id}")
async def delete_message(chatroom_id: str, message_id: str):
    """Deletes the specified message from a specific chatroom."""
    try:
        supabase = get_supabase()

        # Clean up message attachments
        attachments_response = (
            supabase.table("attachments")
            .select("attachment_id")
            .eq("message_id", message_id)
            .execute()
        )

        if attachments_response.data:
            attachments_paths = [f"{chatroom_id}/{att['attachment_id']}" for att in attachments_response.data]
            (
                supabase.storage
                .from_("attachments")
                .remove(attachments_paths)
            )

        # Delete the message entry in DB
        (
            supabase.table("messages")
            .delete()
            .eq("message_id", message_id)
            .execute()
        )

        logger.info(f"DELETE - {router.prefix}/{chatroom_id}/{message_id}\nMessage deleted successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Message deleted successfully",
                "old_message_id": message_id,
                "chatroom_id": chatroom_id
            }
        )
    except Exception as e:
        logger.error(f"DELETE - {router.prefix}/{chatroom_id}/{message_id}\nError deleting message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.detail if hasattr(e, 'detail') else str(e)
        )
