import logging

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.dependencies import get_supabase

router = APIRouter(
    prefix="/api/invites",
    tags=["invites"],
)

logger = logging.getLogger(__name__)


class AcceptInviteRequest(BaseModel):
    user_id: str
    invite_id: str


class RejectInviteRequest(BaseModel):
    user_id: str
    invite_id: str


class SendInviteRequest(BaseModel):
    user_id: str
    recipient_username: str
    chatroom_id: str


class InviteResponse(BaseModel):
    invite_id: str
    sender_username: str
    chatroom_id: str
    chatroom_name: str
    status: str
    created_at: str


@router.post("/accept")
async def accept_invite(request: AcceptInviteRequest):
    """Accept an invite and add user to chatroom members"""
    try:
        supabase = get_supabase()

        logger.info(f"POST - {router.prefix}/accept\nUser {request.user_id} accepting invite {request.invite_id}")

        # Verify the invite belongs to the current user and is pending
        invite_check = (
            supabase.table("invites")
            .select("chatroom_id, status, recipient_id")
            .eq("invite_id", request.invite_id)
            .execute()
        )

        if not invite_check.data or len(invite_check.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invite not found"
            )

        invite_data = invite_check.data[0]

        # Verify the invite belongs to the current user
        if invite_data["recipient_id"] != request.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only accept your own invites"
            )

        # Verify the invite is still pending
        if invite_data["status"] != "PENDING":  # Either ACCEPTED or REJECTED
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invite has already been {invite_data['status'].lower()}"
            )

        chatroom_id = invite_data["chatroom_id"]

        # Check if user is already a member (race condition protection)
        existing_member = (
            supabase.table("members")
            .select("user_id")
            .eq("user_id", request.user_id)
            .eq("chatroom_id", chatroom_id)
            .execute()
        )

        if existing_member.data and len(existing_member.data) > 0:
            # Update invite status to accepted even if already a member
            supabase.table("invites").update({
                "status": "ACCEPTED"
            }).eq("invite_id", request.invite_id).execute()

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": "You are already a member of this chatroom"}
            )
        
        # Update invite status to ACCEPTED
        invite_response = (
            supabase.table("invites")
            .update({
                "status": "ACCEPTED"
            })
            .eq("invite_id", request.invite_id)
            .execute()
        )

        if not invite_response.data or len(invite_response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update invite status"
            )

        # Add user to members table
        member_response = (
            supabase.table("members")
            .insert({
                "user_id": request.user_id,
                "chatroom_id": chatroom_id
            })
            .execute()
        )

        if not member_response.data:
            # Rollback invite status if member insertion fails
            supabase.table("invites").update({
                "status": "PENDING"
            }).eq("invite_id", request.invite_id).execute()

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add user to chatroom"
            )

        logger.info(f"POST - {router.prefix}/accept\nSuccessfully accepted invite {request.invite_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Invite accepted successfully"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"POST - {router.prefix}/accept\nError accepting invite: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to accept invite: {str(e)}"
        )


@router.post("/reject")
async def reject_invite(request: RejectInviteRequest):
    """Reject an invite"""
    try:
        supabase = get_supabase()

        logger.info(f"POST - {router.prefix}/reject\nUser {request.user_id} rejecting invite {request.invite_id}")

        # Verify the invite belongs to the current user and is pending
        invite_check = (
            supabase.table("invites")
            .select("status, recipient_id")
            .eq("invite_id", request.invite_id)
            .execute()
        )

        if not invite_check.data or len(invite_check.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invite not found"
            )
        
        invite_data = invite_check.data[0]
        
        # Verify the invite belongs to the current user
        if invite_data["recipient_id"] != request.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only reject your own invites"
            )
        
        # Verify the invite is still pending
        if invite_data["status"] != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invite has already been {invite_data['status'].lower()}"
            )
        
        # Update invite status to REJECTED
        response = (
            supabase.table("invites")
            .update({
                "status": "REJECTED"
            })
            .eq("invite_id", request.invite_id)
            .execute()
        )

        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update invite status"
            )
        
        logger.info(f"POST - {router.prefix}/reject\nSuccessfully rejected invite {request.invite_id}")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Invite rejected successfully"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"POST - {router.prefix}/reject\nError rejecting invite: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject invite: {str(e)}"
        )


@router.post("/send")
async def send_invite(request: SendInviteRequest):
    """Send an invite to a user"""
    try:
        supabase = get_supabase()

        logger.info(f"POST - {router.prefix}/send\nSending invite from {request.user_id} to {request.recipient_username} for chatroom {request.chatroom_id}")

        # Get recipient user ID by username
        user_response = (
            supabase.table("users")
            .select("user_id")
            .eq("username", request.recipient_username)
            .execute()
        )

        if not user_response.data or len(user_response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        recipient_id = user_response.data[0]["user_id"]

        # Prevent self-invitation
        if recipient_id == request.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot invite yourself to a chatroom"
            )

        # Check if user is already a member
        member_response = (
            supabase.table("members")
            .select("user_id")
            .eq("user_id", recipient_id)
            .eq("chatroom_id", request.chatroom_id)
            .execute()
        )

        if member_response.data and len(member_response.data) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this chatroom"
            )

        # Check if there's already a pending invite for the current chatroom
        existing_invite_response = (
            supabase.table("invites")
            .select("invite_id")
            .eq("recipient_id", recipient_id)
            .eq("chatroom_id", request.chatroom_id)
            .eq("status", "PENDING")
            .execute()
        )

        if existing_invite_response.data and len(existing_invite_response.data) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="There is already a pending invite for this user"
            )

        # Create the invite
        invite_response = (
            supabase.table("invites")
            .insert({
                "sender_id": request.user_id,
                "recipient_id": recipient_id,
                "chatroom_id": request.chatroom_id,
                "status": "PENDING"
            })
            .execute()
        )

        if not invite_response.data or len(invite_response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create invite"
            )

        logger.info(f"POST - {router.prefix}/send\nSuccessfully sent invite {invite_response.data[0]['invite_id']}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Invite sent successfully",
                "invite_id": invite_response.data[0]["invite_id"]
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"POST - {router.prefix}/send\nError sending invite: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send invite: {str(e)}"
        )


@router.get("/{user_id}")
async def get_pending_invites(user_id: str):
    """Get all pending invites for a user"""
    try:
        supabase = get_supabase()

        logger.info(f"GET - {router.prefix}/{user_id}\nFetching pending invites")

        response = supabase.rpc("get_user_pending_invites", {"p_user_id": user_id}).execute()

        if response.data is None:
            response.data = []

        logger.info(f"GET - {router.prefix}/{user_id}\nFound {len(response.data)} pending invite{'s' if len(response.data) != 1 else ''}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"invites": response.data}
        )

    except Exception as e:
        logger.error(f"GET - {router.prefix}/{user_id}\nError fetching invites: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch invites: {str(e)}"
        )
