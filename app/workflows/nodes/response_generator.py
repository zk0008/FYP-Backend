import logging
from datetime import datetime

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

    def _build_system_message(self, state: ChatState) -> None:
        """
        Build system message with context information from retrieved chunks and web search results, if applicable.
        """
        use_rag_query = state.get("use_rag_query", False)
        use_web_search = state.get("use_web_search", False)

        if use_rag_query:
            document_chunks = state.get("document_chunks", [])
            if document_chunks:
                chunks_text = "\n\n".join([
                    f"Filename: {chunk["filename"]}\nRRF score: {round(chunk["rrf_score"], 3)}\nContent: {chunk["content"]}"
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
        else:
            chunks_section = "<document_chunks>\n<!- RAG query not enabled -->\n</document_chunks>"

        # TODO: Web search results
        if use_web_search:
            web_results = state.get("web_results", [])
            if web_results:
                search_results_text = "\n\n".join([
                    f"Title: {result['title']}\nLink: {result['link']}\nSnippet: {result['snippet']}"
                    for result in web_results
                ])
                search_results_section = f"<web_search_results>\n{search_results_text}\n</web_search_results>"
            else:
                search_results_section = "<web_search_results>No web search results available.</web_search_results>"
        else:
            search_results_section = "<web_search_results>\n<!- Web search not enabled -->\n</web_search_results>"

        self.system_message = SystemMessage(
            content=f"""
                You are GroupGPT, a helpful AI assistant in a group chat. Your task is to respond to the user's query comprehensively and naturally using all available context.

                The current date and time is {datetime.now().strftime("%A, %B %-m, %Y at %I:%M:%S %p")}.

                <instructions>
                1. Use the conversation history to understand the context and flow of prior discussion.
                1.1. The conversation history consists of multiple users and you. You are the AI, while the users' messages are formatted as "{{username}}: {{message_content}}".
                1.2. You must keep track of the contexts of each individual user within the chatroom.
                1.3. Do not start your responses with "GroupGPT:" as that is just a label for your messages in the chat history.

                2. **MANDATORY SOURCE CITATION**: You MUST cite sources for ANY factual claims, data, or information that comes from the provided context.
                2.1. For document references: Use format "[{{filename}}]" immediately after the relevant information.
                2.2. For web search results: Use format "[{{site_name}} - {{url}}]" immediately after the relevant information.
                2.3. If you reference multiple sources in one response, cite each one separately.
                2.4. Do NOT provide information from the context without proper citation.

                3. Keep the tone conversational and appropriate for a group chat, but never omit required citations.

                4. If the context does not contain enough information to answer the query, explicitly state this and suggest what additional information might be needed.
                4.1. If the user did not select the RAG query option, suggest that they enable it to retrieve relevant document chunks.
                4.2. If the user did not select the web search option, suggest that they enable it to retrieve up-to-date information from the web.

                5. Format your response clearly and concisely, ensuring citations are easily identifiable.

                **CRITICAL**: Every piece of information derived from the provided context MUST include a citation. Failure to cite sources when using contextual information is not acceptable.
                </instructions>

                {chunks_section}

                {search_results_section}

                <citation_examples>
                Good examples:
                - "According to the quarterly report, sales increased by 15% [Q3_Report.pdf]"
                - "The latest research shows that remote work productivity has improved [Harvard Business Review - https://hbr.org/remote-work-study]"

                Bad examples:
                - "According to the quarterly report, sales increased by 15%" (missing citation)
                - "Sales increased by 15% (from Q3 report)" (improper citation format)
                </citation_examples>
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

        self._build_system_message(state)

        # Build message sequence
        messages = []
        messages.append(self.system_message)

        if chat_history:
            messages.extend(chat_history)

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
