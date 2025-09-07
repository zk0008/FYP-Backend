import logging

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.dependencies import get_supabase

router = APIRouter(
    prefix="/api/invites",
    tags=["invites"],
)

logger = logging.getLogger(__name__)


class UpdateInviteRequest(BaseModel):
    status: str  # "ACCEPTED" or "REJECTED"


class SendInviteRequest(BaseModel):
    recipient_username: str
    chatroom_id: str


class InviteResponse(BaseModel):
    invite_id: str
    sender_username: str
    chatroom_id: str
    chatroom_name: str
    status: str
    created_at: str


@router.get("")
async def get_pending_invites(request: Request):
    """Get all pending invites for a user"""
    try:
        user_id = request.state.user_id
        supabase = get_supabase()

        response = supabase.rpc("get_user_pending_invites", {"p_user_id": user_id}).execute()

        if response.data is None:
            response.data = []

        logger.info(f"GET - {router.prefix}\nFound {len(response.data)} pending invite{'s' if len(response.data) != 1 else ''} for {user_id}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response.data
        )

    except Exception as e:
        logger.error(f"GET - {router.prefix}\nError fetching invites: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.detail if hasattr(e, 'detail') else str(e)
        )


@router.post("")
async def send_invite(request: Request, body: SendInviteRequest):
    """Send an invite to a user"""
    try:
        user_id = request.state.user_id
        supabase = get_supabase()

        logger.info(f"POST - {router.prefix}\nSending invite from {user_id} to {body.recipient_username} for chatroom {body.chatroom_id}")

        # Get recipient user ID by username
        user_response = (
            supabase.table("users")
            .select("user_id")
            .eq("username", body.recipient_username)
            .execute()
        )

        if not user_response.data or len(user_response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipient not found. Please check the username and try again."
            )

        recipient_id = user_response.data[0]["user_id"]

        # Prevent self-invitation
        if recipient_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot invite yourself to the chatroom."
            )

        # Check if recipient is already a member
        member_response = (
            supabase.table("members")
            .select("user_id")
            .eq("user_id", recipient_id)
            .eq("chatroom_id", body.chatroom_id)
            .execute()
        )

        if member_response.data and len(member_response.data) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"'{body.recipient_username}' is already a member of chatroom '{body.chatroom_id}'."
            )

        # Check if there's already a pending invite for the current chatroom
        existing_invite_response = (
            supabase.table("invites")
            .select("invite_id")
            .eq("recipient_id", recipient_id)
            .eq("chatroom_id", body.chatroom_id)
            .eq("status", "PENDING")
            .execute()
        )

        if existing_invite_response.data and len(existing_invite_response.data) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"'{body.recipient_username}' has already been invited to join chatroom '{body.chatroom_id}'. Please wait for them to respond."
            )

        # Create the invite
        invite_response = (
            supabase.table("invites")
            .insert({
                "sender_id": user_id,
                "recipient_id": recipient_id,
                "chatroom_id": body.chatroom_id,
                "status": "PENDING"
            })
            .execute()
        )

        if not invite_response.data or len(invite_response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create invite."
            )

        logger.info(f"POST - {router.prefix}\nSuccessfully sent invite {invite_response.data[0]['invite_id']}")

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Invite sent successfully",
                "invite_id": invite_response.data[0]["invite_id"]
            }
        )

    except Exception as e:
        logger.error(f"POST - {router.prefix}\nError sending invite: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.detail if hasattr(e, 'detail') else str(e)
        )


@router.put("/{invite_id}")
async def update_invite(request: Request, invite_id: str, body: UpdateInviteRequest):
    """Update the status of an invite (ACCEPTED or REJECTED)"""
    try:
        user_id = request.state.user_id
        supabase = get_supabase()

        logger.info(f"PUT - {router.prefix}/{invite_id}\nUser {user_id} updating invite {invite_id} to {body.status}")

        if body.status not in ["ACCEPTED", "REJECTED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Must be either 'ACCEPTED' or 'REJECTED'"
            )

        # Verify the invite belongs to the current user and is pending
        invite_check = (
            supabase.table("invites")
            .select("status, recipient_id")
            .eq("invite_id", invite_id)
            .execute()
        )

        if not invite_check.data or len(invite_check.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invite not found"
            )

        invite_data = invite_check.data[0]

        # Verify the invite belongs to the current user
        if invite_data["recipient_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own invites"
            )

        # Verify the invite is still pending
        if invite_data["status"] != "PENDING":  # Either ACCEPTED or REJECTED
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invite has already been {invite_data['status'].lower()}"
            )

        # Update the invite status
        response = (
            supabase.table("invites")
            .update({
                "status": body.status
            })
            .eq("invite_id", invite_id)
            .execute()
        )

        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update invite status"
            )

        if body.status == "ACCEPTED":
            # Check if user is already a member (race condition protection)
            existing_member = (
                supabase.table("members")
                .select("user_id")
                .eq("user_id", user_id)
                .eq("chatroom_id", response.data[0]["chatroom_id"])
                .execute()
            )

            if existing_member.data and len(existing_member.data) > 0:
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={"message": "You are already a member of this chatroom"}
                )
            else:
                # Add user to members table
                member_response = (
                    supabase.table("members")
                    .insert({
                        "user_id": user_id,
                        "chatroom_id": response.data[0]["chatroom_id"]
                    })
                    .execute()
                )

                if not member_response.data:
                    # Rollback invite status if member insertion fails
                    supabase.table("invites").update({
                        "status": "PENDING"
                    }).eq("invite_id", invite_id).execute()

                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to add user to chatroom"
                    )
        elif body.status == "REJECTED":
            # No additional action needed for rejection
            pass

        logger.info(f"PUT - {router.prefix}/{invite_id}\nSuccessfully updated invite {invite_id} to {body.status}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Invite {body.status.lower()} successfully"}
        )

    except Exception as e:
        logger.error(f"PUT - {router.prefix}/{invite_id}\nError updating invite {invite_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update invite"
        )
