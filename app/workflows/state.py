from typing import Dict, List, TypedDict
from langchain_core.messages import AIMessage, HumanMessage


class ChatState(TypedDict):
    """
    Represents the state of the chat, including the chat history and any relevant document chunks.
    """
    username: str  # Username of the user who sent the message
    chatroom_id: str  # Unique identifier for the chatroom, for fetching history
    query: str  # Query sent by the user
    chat_history: List[AIMessage | HumanMessage]  # List of chat messages exchanged in the chatroom
    files_data: List[Dict[str, str]]  # List of files attached by the user, each dict contains mime_type and base64 data
    final_response: str  # Final response to be returned to the user
