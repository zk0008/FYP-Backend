import logging

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.dependencies import get_supabase

router = APIRouter(
    prefix="/api/chatrooms",
    tags=["chatrooms"],
)

logger = logging.getLogger(__name__)


class CreateChatroomRequest(BaseModel):
    name: str


class EditChatroomRequest(BaseModel):
    name: str


@router.get("/user/{user_id}")
async def get_chatrooms(user_id: str):
    """Retrieves the chatrooms for a specific user."""
    try:
        supabase = get_supabase()

        response = supabase.rpc("get_user_chatrooms_ordered", {"p_user_id": user_id}).execute()

        if response.data is None:
            response.data = []

        logger.info(f"GET - {router.prefix}/user/{user_id}\nFound {len(response.data)} chatroom{'s' if len(response.data) != 1 else ''} for user {user_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response.data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET - {router.prefix}/user/{user_id}\nError fetching chatrooms: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch chatrooms: {str(e)}"
        )


@router.get("/{chatroom_id}")
async def get_chatroom(chatroom_id: str):
    """Retrieves a specific chatroom."""
    try:
        supabase = get_supabase()

        response = (
            supabase.table("chatrooms")
            .select("chatroom_id, name, creator_id")
            .eq("chatroom_id", chatroom_id)
            .single()
            .execute()
        )

        if response.data is None:
            logger.warning(f"GET - {router.prefix}/{chatroom_id}\nChatroom not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatroom not found")

        logger.info(f"GET - {router.prefix}/{chatroom_id}\nFound chatroom: {response.data.name}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response.data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET - {router.prefix}/{chatroom_id}\nError fetching chatroom: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch chatroom: {str(e)}"
        )


@router.post("/user/{user_id}")
async def create_chatroom(user_id: str, request: CreateChatroomRequest):
    """Creates a new chatroom."""
    try:
        supabase = get_supabase()

        # Insert new chatroom entry into DB
        chatroom_response = (
            supabase.table("chatrooms")
            .insert({
                "creator_id": user_id,
                "name": request.name
            })
            .execute()
        )

        # Add creator as member of the chatroom
        if chatroom_response.data:
            chatroom_id = chatroom_response.data[0]["chatroom_id"]
            supabase.table("members").insert({
                "chatroom_id": chatroom_id,
                "user_id": user_id
            }).execute()

        logger.info(f"POST - {router.prefix}/\nUser {user_id} created chatroom: {request.name}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"chatroom_id": chatroom_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"POST - {router.prefix}/\nError creating chatroom: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create chatroom: {str(e)}"
        )


@router.put("/{chatroom_id}")
async def edit_chatroom(chatroom_id: str, request: EditChatroomRequest):
    """Edits an existing chatroom."""
    try:
        supabase = get_supabase()

        response = (
            supabase.table("chatrooms")
            .update({"name": request.name})
            .eq("chatroom_id", chatroom_id)
            .execute()
        )

        if response.data is None or len(response.data) == 0:
            logger.warning(f"PUT - {router.prefix}/{chatroom_id}\nChatroom not found for update")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatroom not found")

        logger.info(f"PUT - {router.prefix}/{chatroom_id}\nUpdated chatroom name to: {request.name}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Chatroom updated successfully",
                "chatroom_id": chatroom_id,
                "new_name": request.name
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PUT - {router.prefix}/{chatroom_id}\nError updating chatroom: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update chatroom: {str(e)}"
        )


@router.delete("/{chatroom_id}")
async def delete_chatroom(chatroom_id: str):
    """Deletes a chatroom."""
    try:
        supabase = get_supabase()

        # Clean up remaining document files in the chatroom (raw files)
        documents_response = (
            supabase.table("documents")
            .select("document_id")
            .eq("chatroom_id", chatroom_id)
            .execute()
        )

        documents_paths = [f"{chatroom_id}/{doc['document_id']}" for doc in documents_response.data]
        documents_paths.append(chatroom_id)  # Delete chatroom folder from storage
        (
            supabase.storage
            .from_("knowledge-bases")
            .remove(documents_paths)
        )

        # Clean up remaining attachment files in the chatroom (raw files)
        attachments_response = supabase.rpc("get_chatroom_attachments", {"p_chatroom_id": chatroom_id}).execute()

        if attachments_response.data:
            attachments_paths = [f"{chatroom_id}/{att['attachment_id']}" for att in attachments_response.data]
            attachments_paths.append(chatroom_id)  # Delete chatroom folder from storage
            (
                supabase.storage
                .from_("attachments")
                .remove(attachments_paths)
            )

        # Delete the chatroom entry in DB
        # Deletion of other associated data such as messages, invites, and document entries are cascaded
        (
            supabase.table("chatrooms")
            .delete()
            .eq("chatroom_id", chatroom_id)
            .execute()
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Chatroom deleted successfully",
                "old_chatroom_id": chatroom_id
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DELETE - {router.prefix}/{chatroom_id}\nError deleting chatroom: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chatroom: {str(e)}"
        )


@router.delete("/{chatroom_id}/user/{user_id}")
async def remove_member(chatroom_id: str, user_id: str):
    """Removes a user from a chatroom (i.e., leaving the chatroom)."""
    try:
        supabase = get_supabase()

        # Delete user from chatroom members
        response = (
            supabase.table("members")
            .delete()
            .eq("chatroom_id", chatroom_id)
            .eq("user_id", user_id)
            .execute()
        )

        if response.data is None or len(response.data) == 0:
            logger.warning(f"DELETE - {router.prefix}/{chatroom_id}/user/{user_id}\nUser not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        logger.info(f"DELETE - {router.prefix}/{chatroom_id}/user/{user_id}\nRemoved user {user_id} from chatroom {chatroom_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "User removed successfully"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DELETE - {router.prefix}/{chatroom_id}/user/{user_id}\nError removing member: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove member: {str(e)}"
        )
