from pydantic import BaseModel

class GroupGPTRequest(BaseModel):
    username: str
    chatroom_id: str
    content: str
