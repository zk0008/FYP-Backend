from pydantic import BaseModel

class GroupGPTRequest(BaseModel):
    username: str
    chatroom_id: str
    content: str
    use_rag_query: bool
    use_web_search: bool
