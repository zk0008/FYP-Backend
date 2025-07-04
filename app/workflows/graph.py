import logging

from langchain_openai import OpenAIEmbeddings
from langgraph.graph import END, START, StateGraph

from app.constants import EMBEDDING_MODEL_NAME
from app.dependencies import get_supabase
from app.llms import gemini_25_flash
from .nodes import (
    ChunkRetriever,
    ChunkSummarizer,
    HistoryFetcher,
    ResponseGenerator,
    WebResultSummarizer,
    WebSearcher
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
        self.web_result_summarizer = WebResultSummarizer()
        self.web_searcher = WebSearcher()

        # Build graph
        self.graph = self._build_graph()

        self.logger = logging.getLogger(__name__)

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        """
        workflow = StateGraph(ChatState)

        # TODO: To summarize or not to summarize? Summarizing reduces the amount of data passed to the LLM, but may lose some details.
        # Add nodes
        workflow.add_node("chunk_retriever", self.chunk_retriever)
        # workflow.add_node("chunk_summarizer", self.chunk_summarizer)
        workflow.add_node("history_fetcher", self.history_fetcher)
        workflow.add_node("response_generator", self.response_generator, defer=True)
        # workflow.add_node("web_result_summarizer", self.web_result_summarizer)
        workflow.add_node("web_searcher", self.web_searcher)

        ### Workflow Structure ###
        # Parallel execution of fetching chat history, retrieving relevant chunks, and searching the web
        def route_from_start(state):
            use_rag = state.get("use_rag_query", False)
            use_web = state.get("use_web_search", False)

            # Always fetch history
            next_nodes = ["history_fetcher"]

            # Chunk retrieval and web searching are conditional
            if use_rag:
                next_nodes.append("chunk_retriever")
            if use_web:
                next_nodes.append("web_searcher")

            return next_nodes

        workflow.add_conditional_edges(
            START,
            route_from_start,
            {
                "history_fetcher": "history_fetcher",
                "chunk_retriever": "chunk_retriever", 
                "web_searcher": "web_searcher"
            }
        )

        # # After retrieving chunks, summarize them first before generating the response
        # workflow.add_edge("chunk_retriever", "chunk_summarizer")

        # # After searching the web, summarize the results first before generating the response
        # workflow.add_edge("web_searcher", "web_result_summarizer")

        workflow.add_edge("history_fetcher", "response_generator")
        workflow.add_edge("chunk_retriever", "response_generator")
        workflow.add_edge("web_searcher", "response_generator")
        # workflow.add_edge("chunk_summarizer", "response_generator")
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
