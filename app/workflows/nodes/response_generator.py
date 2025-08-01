import logging
from datetime import datetime
from typing import Dict, List

from langchain_core.messages import SystemMessage, ToolMessage
from langchain_google_vertexai.chat_models import ChatVertexAI
from langchain_openai.chat_models.base import ChatOpenAI
from supabase import Client

from app.workflows.state import ChatState
from app.workflows.tools import (
    ArxivSearchTool,
    PythonREPLTool,
    WebSearchTool
)
from app.dependencies import get_settings


class ResponseGenerator:
    MAX_TOOL_CALLS = 5

    def __init__(self, supabase: Client, llm: ChatOpenAI | ChatVertexAI):
        self.supabase = supabase

        # Initialize tools
        self.arxiv_search_tool = ArxivSearchTool()
        self.python_repl_tool = PythonREPLTool()
        self.web_search_tool = WebSearchTool()

        self.llm = llm.bind_tools([
            self.arxiv_search_tool,
            self.python_repl_tool,
            self.web_search_tool
        ])
        self.logger = logging.getLogger(self.__class__.__name__)

    def _build_system_message(self, state: ChatState) -> None:
        """
        Build system message with context information from retrieved chunks and web search results, if applicable.
        """
        document_chunks = state.get("document_chunks", [])
        if document_chunks:
            chunks_text = "\n\n".join([
                f"Filename: {chunk['filename']}\nRRF score: {round(chunk['rrf_score'], 3)}\nContent: {chunk['content']}"
                for chunk in document_chunks
            ])
            chunks_section = f"<document_chunks>\n{chunks_text}\n</document_chunks>"
        else:
            chunks_section = "<document_chunks>No document chunks available.</document_chunks>"

        # chunk_summaries = state.get("chunk_summaries", [])
        # if chunk_summaries:
        #     chunks_text = "\n\n".join([
        #         f"Filename: {chunk.filename}\nRRF score: {round(chunk.rrf_score, 3)}\nContent: {chunk.content}"
        #         for chunk in chunk_summaries
        #     ])
        #     chunks_section = f"<document_chunks>\n{chunks_text}\n</document_chunks>"
        # else:
        #     chunks_section = "<document_chunks>No document chunks available.</document_chunks>"

        # TODO: Add executed code to generated response
        self.system_message = SystemMessage(
            content=f"""
                You are GroupGPT, a helpful AI assistant in a group chat. Your task is to respond to the user's query comprehensively and naturally using all available context.

                The current date and time is {datetime.now().strftime("%A, %B %-m, %Y at %I:%M:%S %p")}.

                <instructions>
                1. Use the conversation history to understand the context and flow of prior discussion.
                1.1. The conversation history consists of multiple users and you. You are the AI, while the users' messages are formatted as "{{username}}: {{message_content}}".
                1.2. You must keep track of the contexts of each individual user within the chatroom.
                1.3. Do not start your responses with "GroupGPT:" as that is just a label for your messages in the chat history.

                2. **TOOL USAGE**: You have access to the following tools:
                2.1. *web_search*: Use this tool to search the web about any topic. This is useful when the user asks about up-to-date information, or when the provided context and your training data doesn't contain sufficient information to answer the query.
                2.2. *python_repl*: Use this tool to execute Python code for calculations, data processing, or any other programming-related tasks. Use the `print()` function to get required results from this tool.
                2.3. *arxiv_search*: Use this tool to search arXiv for academic papers related to the query. This is useful when the user asks about research papers or articles on a specific topic.

                3. **MANDATORY SOURCE CITATION**: You MUST cite sources for ANY factual claims, data, or information that comes from the provided context.
                3.1. For document references: If page or slide numbers are available, use format "[{{filename}}, page/slide {{page/slide number}}]" immediately after the relevant information. Otherwise, use format "[{{filename}}]".
                3.2. For web search results: Use format "[[{{site_name}}]({{link}})]" immediately after the relevant information. Present the site name as it appears in the link. This ensures that a clickable link is created in the chat.
                3.3. For arXiv search results: Use format "[[arXiv](https://arxiv.org/abs/{{arxiv_id}})]" immediately after the relevant information.
                3.4. If you reference multiple sources in one response, cite each one separately.
                3.5. Do NOT provide information from the context without proper citation.

                4. Keep the tone conversational and appropriate for a group chat, but never omit required citations.

                5. If the context does not contain enough information to answer the query, explicitly state this and suggest what additional information might be needed.

                6. Format your response clearly and concisely, ensuring citations are easily identifiable.

                **CRITICAL**: Every piece of information derived from the provided context MUST include a citation. Failure to cite sources when using contextual information is not acceptable.
                </instructions>

                <document_chunks>No document chunks available.</document_chunks>

                <citation_examples>
                Good examples:
                - "According to the quarterly report, sales increased by 15% [Q3_Report.pdf, page 4]."
                - "Object-oriented programming is a programming paradigm based on the concept of objects [OOP_Lecture_Recording.mp3]."
                - "The latest research shows that remote work productivity has improved by 13% [[Harvard Business Review](https://hbr.org/remote-work-study)][[arXiv](https://arxiv.org/abs/2101.00001)]."

                Bad examples:
                - "According to the quarterly report, sales increased by 15%." (missing citation)
                - "Sales increased by 15% (from Q3 report)." (improper citation format)
                </citation_examples>
            """
        )

    def _execute_tool_calls(self, tool_call: Dict[str, str]) -> ToolMessage:
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

    def _handle_tool_calls(self, messages: List) -> List:
        """Handle tool calls and add tool responses to message history."""
        iteration = 0

        while iteration < self.MAX_TOOL_CALLS:
            # Get the latest response
            response = self.llm.invoke(messages)
            messages.append(response)

            # Check if the response contains tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_message = self._execute_tool_calls(tool_call)
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
        chat_history = state.get("chat_history", [])

        self._build_system_message(state)

        # Build message sequence
        messages = []
        messages.append(self.system_message)

        if chat_history:
            messages.extend(chat_history)

        try:
            messages, response = self._handle_tool_calls(messages)
            final_response = response.content.strip()

            if not final_response:
                final_response = "I apologize, but I encountered an error while generating a response. Please try again."

            self.logger.debug("Successfully generated response")
            self.logger.debug(response)
        except Exception as e:
            self.logger.exception(e)
            final_response = "I apologize, but I encountered an error while generating a response. Please try again."

        state["final_response"] = final_response
        self._insert_response(
            chatroom_id=state["chatroom_id"],
            content=state["final_response"]
        )
        return state
