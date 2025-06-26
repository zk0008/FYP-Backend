import logging

from langchain_openai import OpenAIEmbeddings
from supabase import Client

from app.workflows.state import ChatState


class ChunkRetriever:
    def __init__(self, supabase: Client, embedding_model: OpenAIEmbeddings, num_relevant_chunks: int = 5):
        self.supabase = supabase
        self.embedding_model = embedding_model
        self.num_relevant_chunks = num_relevant_chunks
        self.logger = logging.getLogger(self.__class__.__name__)

    def __call__(self, state: ChatState) -> dict:
        query_text = state["query"]
        chatroom_id = state["chatroom_id"]
        document_chunks = []

        try:
            query_embedding = self.embedding_model.embed_query(query_text)
            response = (
                self.supabase.rpc("hybrid_search", {
                    "p_chatroom_id": chatroom_id,
                    "query_embedding": query_embedding,
                    "search_query": query_text,
                    "match_count": self.num_relevant_chunks
                })
                .execute()
            )
            document_chunks.extend(response.data)

            self.logger.debug("Successfully retrieved relevant chunks")
        except Exception as e:
            self.logger.exception(e)

        return {"document_chunks": document_chunks}
