import base64
import logging
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from fastapi import (
    APIRouter,
    HTTPException,
    File,
    Form,
    Request,
    status,
    UploadFile
)
from fastapi.responses import JSONResponse

from app.dependencies import get_supabase
from app.workflows.graph import GroupGPTGraph

router = APIRouter(
    prefix="/api/messages",
    tags=["messages"],
)

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TMP_FILES_DIR = PROJECT_ROOT / "tmp_files"


@router.post("")
async def send_message(
    request: Request,
    chatroom_id: str,
    content: str = Form(...),
    attachments: Optional[List[UploadFile]] = File(None)
) -> JSONResponse:
    """Sends a message to a chatroom, handling both regular messages and GroupGPT invocations."""
    try:
        username = request.state.username
        user_id = request.state.user_id
        supabase = get_supabase()
        
        logger.info(
            f"POST - {router.prefix}\n" +
            f"Sending message to chatroom {chatroom_id}\n" +
            f"User: {username} (ID: {user_id})\n" +
            f"Content: {content[:50]}{'...' if len(content) > 50 else ''}\n" +
            f"Attachments: {len(attachments) if attachments else 0} files"
        )

        # Insert message into database
        message_data = {
            "chatroom_id": chatroom_id,
            "content": content.strip(),
            "sender_id": user_id,
            "has_attachments": attachments is not None and len(attachments) > 0
        }

        message_response = (
            supabase.table("messages")
            .insert(message_data)
            .execute()
        )

        if not message_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to insert message into database"
            )

        message_id = message_response.data[0]["message_id"]

        # Handle attachments if present
        if attachments and len(attachments) > 0:
            try:
                await _handle_attachments(
                    supabase=supabase,
                    chatroom_id=chatroom_id,
                    message_id=message_id,
                    attachments=attachments
                )
            except Exception as e:
                # Rollback message if attachment handling fails
                supabase.table("messages").delete().eq("message_id", message_id).execute()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to handle attachments: {str(e)}"
                )

        # Handle GroupGPT invocation if needed
        is_groupgpt_message = "@groupgpt" in content.lower()
        if is_groupgpt_message:
            try:
                await _invoke_groupgpt(
                    username=username,
                    chatroom_id=chatroom_id,
                    content=content,
                    attachments=attachments
                )
            except Exception as e:
                logger.error(f"GroupGPT invocation failed: {str(e)}")
                # Message is not rolled back since it is still a valid user message

        logger.debug(f"POST - {router.prefix}\nMessage sent successfully (ID: {message_id})")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Message sent successfully",
                "message_id": message_id
            }
        )
    except Exception as e:
        logger.error(f"POST - {router.prefix}\nError sending message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.detail if hasattr(e, 'detail') else str(e)
        )


async def _handle_attachments(
    supabase,
    chatroom_id: str,
    message_id: str,
    attachments: List[UploadFile]
) -> None:
    """Helper function for handling attachment upload and insertion of database entries."""
    for attachment in attachments:
        attachment_id = str(uuid4())  # Generate a random UUID v4 for attachment ID
        file_content = await attachment.read()

        # Upload to Supabase storage
        storage_path = f"{chatroom_id}/{attachment_id}"
        supabase.storage.from_("attachments").upload(
            path=storage_path,
            file=file_content,
            file_options={
                "content-type": attachment.headers["content-type"],
                "upsert": "true"
            }
        )

        # Insert attachment entry into database
        (
            supabase.table("attachments")
            .insert({
                "attachment_id": attachment_id,
                "message_id": message_id,
                "mime_type": attachment.content_type,
                "filename": attachment.filename
            })
            .execute()
        )


async def _invoke_groupgpt(username: str, chatroom_id: str, content: str, attachments: Optional[List[UploadFile]] = None) -> str:
    """Helper function for invoking GroupGPT with the provided message and attachments."""
    # Remove @groupgpt mention from content
    content_without_mention = content.replace("@groupgpt", "", 1).strip()

    # Prepare files data for GroupGPT
    files_data = []
    if attachments:
        for attachment in attachments:
            # Reset file pointer to beginning
            await attachment.seek(0)
            file_content = await attachment.read()
            base64_content = base64.b64encode(file_content).decode("utf-8")
            
            files_data.append({
                "type": "media",
                "source_type": "base64",
                "mime_type": attachment.content_type,
                "data": base64_content
            })

    # Invoke GroupGPT
    graph = GroupGPTGraph()
    response = await graph.process_query(
        username=username,
        chatroom_id=chatroom_id,
        content=content_without_mention,
        files_data=files_data
    )

    return response


@router.get("")
async def get_messages(chatroom_id: str) -> JSONResponse:
    """Retrieves all messages for a specific chatroom."""
    try:
        supabase = get_supabase()

        messages_response = supabase.rpc("get_chatroom_messages", {"p_chatroom_id": chatroom_id}).execute()

        if messages_response.data is None:
            messages_response.data = []

        logger.debug(f"GET - {router.prefix}\nFound {len(messages_response.data)} message{'s' if len(messages_response.data) != 1 else ''} for chatroom {chatroom_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=messages_response.data
        )
    except Exception as e:
        logger.error(f"GET - {router.prefix}\nError retrieving messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.detail if hasattr(e, 'detail') else str(e)
        )


@router.delete("/{message_id}")
async def delete_message(message_id: str) -> JSONResponse:
    """Deletes the specified message from a specific chatroom."""
    try:
        supabase = get_supabase()

        # Fetch message attachments
        attachments_response = (
            supabase.table("attachments")
            .select("attachment_id")
            .eq("message_id", message_id)
            .execute()
        )

        # Delete message entry in DB
        delete_message_response = (
            supabase.table("messages")
            .delete()
            .eq("message_id", message_id)
            .execute()
        )

        if attachments_response.data and delete_message_response.data:
            chatroom_id = delete_message_response.data[0]['chatroom_id']
            attachments_paths = [f"{chatroom_id}/{att['attachment_id']}" for att in attachments_response.data]
            (
                supabase.storage
                .from_("attachments")
                .remove(attachments_paths)
            )

        logger.debug(f"DELETE - {router.prefix}/{message_id}\nMessage deleted successfully")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Message deleted successfully",
                "old_message_id": message_id
            }
        )
    except Exception as e:
        logger.error(f"DELETE - {router.prefix}/{message_id}\nError deleting message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.detail if hasattr(e, 'detail') else str(e)
        )
