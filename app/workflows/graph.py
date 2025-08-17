import logging
from typing import Dict, List, Optional

from langgraph.graph import END, START, StateGraph

from app.dependencies import get_supabase
from app.llms import gemini_25_flash

from .nodes import FilesAttacher, HistoryFetcher, ResponseGenerator
from .state import ChatState


class GroupGPTGraph:
    def __init__(self):
        self.supabase = get_supabase()  # Initialize Supabase client for DB operations

        self.files_attacher = FilesAttacher()  # Responsible for attaching files to messages
        self.history_fetcher = HistoryFetcher(supabase=self.supabase)  # Responsible for fetching chat history
        self.response_generator = ResponseGenerator(supabase=self.supabase, llm=gemini_25_flash)  # Responsible for generating responses

        # Build graph
        self.graph = self._build_graph()

        self.logger = logging.getLogger(__name__)


    def _should_attach_files(self, state: ChatState) -> str:
        attached_files = state.get("files_data", [])
        return "has_attached_files" if len(attached_files) > 0 else "no_attached_files"


    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        """
        workflow = StateGraph(ChatState)

        # TODO: To summarize or not to summarize? Summarizing reduces the amount of data passed to the LLM, but may lose some details.
        # Add nodes
        workflow.add_node("files_attacher", self.files_attacher)
        workflow.add_node("history_fetcher", self.history_fetcher)
        workflow.add_node("response_generator", self.response_generator)

        ### Workflow Structure ###
        workflow.add_edge(START, "history_fetcher")
        workflow.add_conditional_edges(
            "history_fetcher",
            self._should_attach_files,
            {
                "has_attached_files": "files_attacher",
                "no_attached_files": "response_generator"
            }
        )
        workflow.add_edge("files_attacher", "response_generator")
        workflow.add_edge("response_generator", END)

        return workflow.compile()


    async def process_query(
        self,
        username: str,
        chatroom_id: str,
        content: str,
        files_data: Optional[List[Dict[str, str]]] = []  # List of dicts containing mime_type and base64 data
    ) -> str:
        initial_state = ChatState(
            username=username,
            chatroom_id=chatroom_id,
            query=content,
            files_data=files_data,
            chat_history=[]
        )

        final_state = await self.graph.ainvoke(initial_state)
        return final_state["final_response"]
