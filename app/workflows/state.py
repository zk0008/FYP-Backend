import operator
from typing import Annotated, Dict, List, TypedDict
from langchain_core.messages import AIMessage, HumanMessage


class ChatState(TypedDict):
    """
    Represents the state of the chat, including the chat history and any relevant document chunks.
    """
    username: str               # Username of the user who sent the message
    chatroom_id: str            # Unique identifier for the chatroom, for fetching history
    query: str         # Query sent by the user
    chat_history: Annotated[List[AIMessage | HumanMessage], operator.add]
    # "filename": str, "content": str, "distance": float
    document_chunks: Annotated[List[Dict[str, str | float]], operator.add]
    chunk_summaries: Annotated[List[Dict[str, str | float]], operator.add]
    needs_web_search: bool      # Whether chat_history and document_chunks are sufficient to generate a response to user's query
    # "title": str, "url": str, "snippet": str
    web_results: List[Dict[str, str]]
    final_response: str         # Final response to be returned to the user
