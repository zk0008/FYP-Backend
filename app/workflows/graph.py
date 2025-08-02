import logging

from langgraph.graph import END, START, StateGraph

from app.dependencies import get_supabase
from app.llms import gemini_25_flash
from app.models import GroupGPTRequest

from .nodes import HistoryFetcher, ResponseGenerator
from .state import ChatState


class GroupGPTGraph:
    def __init__(self):
        self.supabase = get_supabase()  # Initialize Supabase client for DB operations

        self.history_fetcher = HistoryFetcher(supabase=self.supabase)  # Responsible for fetching chat history
        self.response_generator = ResponseGenerator(supabase=self.supabase, llm=gemini_25_flash)  # Responsible for generating responses

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
        workflow.add_node("history_fetcher", self.history_fetcher)
        workflow.add_node("response_generator", self.response_generator)

        ### Workflow Structure ###
        workflow.add_edge(START, "history_fetcher")
        workflow.add_edge("history_fetcher", "response_generator")
        workflow.add_edge("response_generator", END)

        return workflow.compile()

    async def process_query(self, request: GroupGPTRequest) -> str:
    #     self,
    #     username: str,
    #     chatroom_id: str,
    #     content: str
    # ) -> str:
        initial_state = ChatState(
            username=request.username,
            chatroom_id=request.chatroom_id,
            query=request.content,
            chat_history=[]
        )

        final_state = await self.graph.ainvoke(initial_state)
        return final_state["final_response"]
