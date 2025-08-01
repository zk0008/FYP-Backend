import operator
from typing import Annotated, Dict, List, TypedDict
from langchain_core.messages import AIMessage, HumanMessage


class ChatState(TypedDict):
    """
    Represents the state of the chat, including the chat history and any relevant document chunks.
    """
    username: str                   # Username of the user who sent the message
    chatroom_id: str                # Unique identifier for the chatroom, for fetching history
    query: str                      # Query sent by the user
    chat_history: Annotated[List[AIMessage | HumanMessage], operator.add]

    # RAG-related fields
    document_chunks: Annotated[List[Dict[str, str | float]], operator.add]  # List of document chunks, each with "filename", "content", and "rrf_score"
    # chunk_summaries: Annotated[List[Dict[str, str | float]], operator.add]

    final_response: str             # Final response to be returned to the user
