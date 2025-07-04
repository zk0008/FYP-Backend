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
    use_rag_query: bool = False     # Whether to use RAG for the query
    document_chunks: Annotated[List[Dict[str, str | float]], operator.add]  # List of document chunks, each with "filename", "content", and "rrf_score"
    chunk_summaries: Annotated[List[Dict[str, str | float]], operator.add]

    # Web search-related fields
    use_web_search: bool = False    # Whether to use web search for the query
    web_results: Annotated[List[Dict[str, str]], operator.add]  # List of web search results, each with "title", "link", and "snippet"
    web_result_summaries: Annotated[List[Dict[str, str]], operator.add]

    final_response: str             # Final response to be returned to the user
