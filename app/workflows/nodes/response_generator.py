import logging
from typing import Dict, List

from langchain_core.messages import SystemMessage
from langchain_google_vertexai.chat_models import ChatVertexAI
from langchain_openai.chat_models.base import ChatOpenAI
from supabase import Client

from app.workflows.state import ChatState
from app.dependencies import get_settings


class ResponseGenerator:
    def __init__(self, supabase: Client, llm: ChatOpenAI | ChatVertexAI):
        self.supabase = supabase
        self.llm = llm
        self.logger = logging.getLogger(self.__class__.__name__)

    def _build_system_message(
        self,
        document_chunks: List[Dict[str, str | float]]
    ) -> None:
        """
        Build system message with context information from retrieved chunks.
        """
        chunks_text = "None"        # Default to "None"
        if document_chunks:
            chunks_text = "\n\n".join([f"From {chunk["filename"]} with distance {chunk["distance"]}:\n{chunk["content"]}"
                                       for chunk in document_chunks])

        # TODO: Web search results

        self.system_message = SystemMessage(
            content=f"""
                You are GroupGPT, a helpful AI assistant in a group chat. Your task is to respond to the user's query comprehensively and naturally using all available context.

                <instructions>
                1. Use the conversation history to understand the context and flow of prior discussion.
                  1.1. The conversation history consists of multiple users and you. You are the AI, while the users' messages are formatted as "<username>: <message_content>".
                  1.2. You must keep track of the contexts of each individual user within the chatroom.
                2. Reference information from the provided context and mention sources whenever used.
                  2.1. If a document was referenced, give the name of the referenced file and the similarity distance.
                  2.2. If a web search result was referenced, give the name and URL of the referenced site.
                3. Keep the tone conversational and appropriate for a group chat.
                4. If the context does not contain enough information, let the user know.
                5. Format your response clearly and concisely.
                </instructions>

                <document_chunks>
                {chunks_text}
                </document_chunks>
            """
        )

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
        document_chunks = state.get("document_chunks", [])
        # web_results = state.get("web_results", [])

        self._build_system_message(document_chunks)

        # Build message sequence
        messages = []
        messages.append(self.system_message)

        if chat_history:
            messages.extend(chat_history)       # Includes the user's rewritten query

        try:
            response = self.llm.invoke(messages)
            final_response = response.content.strip()

            self.logger.debug("Successfully generated response")
        except Exception as e:
            self.logger.exception(e)
            final_response = "I apologize, but I encountered an error while generating a response. Please try again."

        state["final_response"] = final_response
        self._insert_response(
            chatroom_id=state["chatroom_id"],
            content=state["final_response"]
        )
        return state
