import logging

from langchain_openai import OpenAIEmbeddings
from langgraph.graph import END, START, StateGraph

from app.constants import EMBEDDING_MODEL_NAME
from app.dependencies import get_supabase
from app.llms import gemini_2_flash_lite, gemini_25_flash
from .nodes import (
    ChunkRetriever,
    ChunkSummarizer,
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
        self.chunk_summarizer = ChunkSummarizer(llm=gemini_25_flash)
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
        workflow.add_node("chunk_summarizer", self.chunk_summarizer)
        workflow.add_node("history_fetcher", self.history_fetcher)
        workflow.add_node("response_generator", self.response_generator, defer=True)

        ### Workflow Structure ###
        # Parallel execution of fetching chat history, retrieving relevant chunks, and searching the web
        # Chunk retrieval and web searching are conditional
        workflow.add_edge(START, "history_fetcher")
        workflow.add_conditional_edges(
            START,
            lambda state: "RAG query" if state["use_rag_query"] else "No RAG query",        # For graph visualization
            {
                "RAG query": "chunk_retriever",
                "No RAG query": "response_generator"
            }
        )
        # workflow.add_conditional_edges(
        #     START,
        #     lambda state: "web_searcher" if state["use_web_search"] else "response_generator",
        # )

        # After retrieving chunks, summarize them first before generating the response
        workflow.add_edge("chunk_retriever", "chunk_summarizer")

        # After searching the web, summarize the results first before generating the response
        # workflow.add_edge("web_searcher", "web_result_summarizer")

        workflow.add_edge("history_fetcher", "response_generator")
        workflow.add_edge("chunk_summarizer", "response_generator")
        # workflow.add_edge("web_result_summarizer", "response_generator")

        # Finally, generate the response
        workflow.add_edge("response_generator", END)

        return workflow.compile()

    async def process_query(
        self,
        username: str,
        chatroom_id: str,
        use_rag_query: bool,
        use_web_search: bool,
        content: str
    ) -> str:
        initial_state = ChatState(
            username=username,
            chatroom_id=chatroom_id,
            query=content,
            chat_history=[],
            # RAG-related fields
            use_rag_query=use_rag_query,
            document_chunks=[],
            chunk_summaries=[],
            # Web search-related fields
            use_web_search=use_web_search,
            web_results=[],
            final_response=""
        )

        final_state = await self.graph.ainvoke(initial_state)
        return final_state["final_response"]
