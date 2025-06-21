import logging

from langchain_openai import OpenAIEmbeddings
from langgraph.graph import END, START, StateGraph

from app.constants import EMBEDDING_MODEL_NAME
from app.dependencies import get_supabase
from app.llms import gemini_2_flash_lite, gemini_25_flash
from .nodes import (
    ChunkRetriever,
    HistoryFetcher,
    ResponseGenerator
)
from .state import ChatState


class GroupGPTGraph:
    def __init__(self):
        # Initialize clients
        self.supabase = get_supabase()
        self.embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL_NAME)

        # Initialize nodes
        self.chunk_retriever = ChunkRetriever(supabase=self.supabase, embedding_model=self.embedding_model)
        self.history_fetcher = HistoryFetcher(supabase=self.supabase)
        self.response_generator = ResponseGenerator(supabase=self.supabase, llm=gemini_25_flash)

        # Build graph
        self.graph = self._build_graph()

        self.logger = logging.getLogger(__name__)

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        """
        workflow = StateGraph(ChatState)

        # Add nodes
        workflow.add_node("chunk_retriever", self.chunk_retriever)
        workflow.add_node("history_fetcher", self.history_fetcher)
        workflow.add_node("response_generator", self.response_generator)

        # Define workflow steps
        # Parallel execution of fetching chat history and retrieving relevant chunks
        workflow.add_edge(START, "history_fetcher")
        workflow.add_edge(START, "chunk_retriever")
        workflow.add_edge("history_fetcher", "response_generator")
        workflow.add_edge("chunk_retriever", "response_generator")
        workflow.add_edge("response_generator", END)

        return workflow.compile()

    async def process_query(self, username: str, chatroom_id: str, content: str) -> str:
        initial_state = ChatState(
            username=username,
            chatroom_id=chatroom_id,
            query=content,
            chat_history=[],
            document_chunks=[],
            needs_web_search=False,
            web_results=[],
            final_response=""
        )

        final_state = await self.graph.ainvoke(initial_state)
        return final_state["final_response"]
