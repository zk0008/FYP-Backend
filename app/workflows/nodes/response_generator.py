import logging
from datetime import datetime
from typing import Dict, List

from langchain_core.messages import SystemMessage, ToolMessage
from langchain_google_vertexai.chat_models import ChatVertexAI
from langchain_openai.chat_models.base import ChatOpenAI
from supabase import Client

from app.dependencies import get_settings
from app.prompts import RESPONSE_GENERATOR_PROMPT
from app.workflows.state import ChatState
from app.workflows.tools import (
    ArxivSearchTool,
    ChunkRetrieverTool,
    PythonREPLTool,
    WebSearchTool
)


class ResponseGenerator:
    MAX_TOOL_CALLS = 10


    def __init__(self, supabase: Client, llm: ChatOpenAI | ChatVertexAI):
        self.supabase = supabase

        # Initialize tools
        self.arxiv_search_tool = ArxivSearchTool()
        self.chunk_retriever_tool = ChunkRetrieverTool()
        self.python_repl_tool = PythonREPLTool()
        self.web_search_tool = WebSearchTool()

        self.llm = llm.bind_tools([
            self.arxiv_search_tool,
            self.chunk_retriever_tool,
            self.python_repl_tool,
            self.web_search_tool
        ])
        self.logger = logging.getLogger(self.__class__.__name__)


    def _execute_tool_calls(self, tool_call: Dict[str, str], chatroom_id: str) -> ToolMessage:
        """
        Executes a single tool call and returns the result as a ToolMessage.
        """
        try:
            if tool_call['name'] == 'web_search':
                tool_result = self.web_search_tool._run(
                    query=tool_call['args']['query'],
                    num_results=tool_call['args'].get('num_results', 5)
                )
            elif tool_call['name'] == 'python_repl':
                tool_result = self.python_repl_tool._run(
                    code=tool_call['args']['code']
                )
            elif tool_call['name'] == 'arxiv_search':
                tool_result = self.arxiv_search_tool._run(
                    query=tool_call['args']['query']
                )
            elif tool_call['name'] == 'chunk_retriever':
                tool_result = self.chunk_retriever_tool._run(
                    chatroom_id=chatroom_id,
                    query=tool_call['args']['query'],
                    num_chunks=tool_call['args'].get('num_chunks', 5)
                )
            else:
                self.logger.warning(f"Unknown tool call: {tool_call['name']}")
                tool_result = f"Unknown tool call: {tool_call['name']}"

            return ToolMessage(
                content=tool_result,
                tool_call_id=tool_call['id']
            )
        except Exception as e:
            self.logger.exception(f"Error executing tool {tool_call['name']}: {e}")
            return ToolMessage(
                content=f"Error executing {tool_call['name']}: {str(e)}",
                tool_call_id=tool_call['id']
            )


    def _handle_tool_calls(self, messages: List, chatroom_id: str) -> List:
        """Handle tool calls and add tool responses to message history."""
        iteration = 0

        while iteration < self.MAX_TOOL_CALLS:
            # Get the latest response
            response = self.llm.invoke(messages)
            messages.append(response)

            # Check if the response contains tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_message = self._execute_tool_calls(tool_call, chatroom_id)
                    messages.append(tool_message)

                iteration += 1
            else:
                # No more tool calls, final response has been generated
                return messages, response

        # Max. iterations reached
        self.logger.warning("Maximum tool call iterations reached without final response.")
        return messages, response


    def _insert_response(
        self,
        chatroom_id: str,
        content: str
    ) -> dict:
        settings = get_settings()
        try:
            response = (
                self.supabase.table("messages")
                .insert({
                    "sender_id": settings.GROUPGPT_USER_ID,
                    "chatroom_id": chatroom_id,
                    "content": content
                })
                .execute()
            )
            return response
        except Exception as e:
            self.logger.exception(e)


    def __call__(self, state: ChatState) -> ChatState:
        """
        Generates the final response using all available information.
        """
        # Build message sequence
        messages = [
            # TODO: Figure out a way to include any executed Python code in generated response
            SystemMessage(
                content=RESPONSE_GENERATOR_PROMPT.format(current_datetime=datetime.now().strftime("%A, %B %-d, %Y at %I:%M:%S %p"))
            )
        ]
        messages.extend(state.get("chat_history", []))

        try:
            messages, response = self._handle_tool_calls(messages, state["chatroom_id"])

            final_response = response.content.strip()

            # Remove any "GroupGPT:" prefix from the final response
            if final_response.startswith("GroupGPT:"):
                final_response = final_response[len("GroupGPT:"):].strip()

            if not final_response:
                final_response = "I apologize, but I encountered an error while generating a response. Please try again."

            self.logger.debug(f"Successfully generated response: {final_response[:50]}")
        except Exception as e:
            self.logger.exception(e)
            final_response = "I apologize, but I encountered an error while generating a response. Please try again."

        try:
            self._insert_response(
                chatroom_id=state["chatroom_id"],
                content=final_response
            )
        except Exception as e:
            self.logger.exception(f"Error inserting response into database: {e}")

        state["final_response"] = final_response
        return state
