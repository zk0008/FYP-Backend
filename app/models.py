from pydantic import BaseModel, Field

from app.constants import MIN_USERNAME_LENGTH, MAX_USERNAME_LENGTH


class GroupGPTRequest(BaseModel):
    username: str = Field(..., min_length=MIN_USERNAME_LENGTH, max_length=MAX_USERNAME_LENGTH)
    chatroom_id: str
    content: str
