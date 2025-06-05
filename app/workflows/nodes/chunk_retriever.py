import logging

# TODO: Possible integration with SupabaseVectorStore
# from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings
from supabase import Client

from app.workflows.state import ChatState


class ChunkRetriever:
    def __init__(self, supabase: Client, embedding_model: OpenAIEmbeddings, num_relevant_chunks: int = 5):
        self.supabase = supabase
        self.embedding_model = embedding_model
        self.num_relevant_chunks = num_relevant_chunks
        self.logger = logging.getLogger(self.__class__.__name__)

    def __call__(self, state: ChatState) -> ChatState:
        query_text = state["rewritten_query"]
        chatroom_id = state["chatroom_id"]
        document_chunks = []

        try:
            query_embedding = self.embedding_model.embed_query(query_text)
            response = (
                self.supabase.rpc("get_similar_embeddings_v2", {
                    "p_chatroom_id": chatroom_id,
                    "query_embedding": query_embedding,
                    "match_count": self.num_relevant_chunks
                })
                .execute()
            )
            document_chunks.extend(response.data)

            self.logger.debug("Successfully retrieved relevant chunks")
        except Exception as e:
            self.logger.exception(e)

        return {"document_chunks": document_chunks}
