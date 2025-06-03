from typing import Dict, List, TypedDict
from langchain_core.messages import AIMessage, HumanMessage


class ChatState(TypedDict):
    """
    Represents the state of the chat, including the chat history and any relevant document chunks.
    """
    username: str               # Username of the user who sent the message
    chatroom_id: str            # Unique identifier for the chatroom, for fetching history
    original_query: str         # Original query sent by the user
    rewritten_query: str        # LLM-rewritten query
    chat_history: List[AIMessage | HumanMessage]
    document_chunks: List[Dict[str, str | float]]  # "filename": str, "content": str, "distance": float
    needs_web_search: bool      # Whether chat_history and document_chunks are sufficient to generate a response to user's query
    web_results: List[Dict[str, str]]  # "title": str, "url": str, "snippet": str
    final_response: str
