import logging

from langchain_openai import OpenAIEmbeddings
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.constants import EMBEDDING_MODEL_NAME
from app.dependencies import get_supabase


class ChunkRetrieverInput(BaseModel):
    """
    Input schema for the Chunk Retriever tool
    """
    chatroom_id: str = Field(..., description="This is a system variable. **Leave this field empty** when calling the tool as it will be set automatically.")
    query: str = Field(..., description="Query to search for relevant document chunks in the knowledge base. Should contain precise keywords and phrases related to the user's original query.")
    num_chunks: int = Field(default=5, description="Number of relevant document chunks to retrieve. Default is 5. Adjust based on the query complexity and expected results.")


class ChunkRetrieverTool(BaseTool):
    """
    Tool for retrieving relevant document chunks from the knowledge base using hybrid search.
    """
    name: str = "chunk_retriever"
    description: str = "Retrieve relevant document chunks from the knowledge base using hybrid search. Use this when you need to find specific information or context from the knowledge base related to a query."
    args_schema: type[BaseModel] = ChunkRetrieverInput

    def _run(self, chatroom_id: str, query: str, num_chunks: int = 5) -> str:
        """
        Searches knowledge base for relevant document chunks and returns the results.
        """
        logger = logging.getLogger(self.__class__.__name__)
        supabase = get_supabase()
        embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL_NAME)

        try:
            query_embedding = embedding_model.embed_query(query)
            response = (
                supabase.rpc("hybrid_search", {
                    "p_chatroom_id": chatroom_id,
                    "query_embedding": query_embedding,
                    "search_query": query,
                    "match_count": int(num_chunks)  # Number of relevant chunks to retrieve
                })
                .execute()
            )
            document_chunks = response.data
            chunks_text = "\n\n".join([
                f"Filename: {chunk['filename']}\nRRF score: {round(chunk['rrf_score'], 3)}\nContent: {chunk['content']}"
                for chunk in document_chunks
            ]) if document_chunks else "No relevant document chunks found."

            logger.debug(f"Chunk retrieval executed with the following parameters:\n"
                         f"Chatroom ID: {chatroom_id}\n"
                         f"Query: {query}\n"
                         f"Number of Chunks: {num_chunks}")
            logger.debug(f"Retrieved document chunks:\n{chunks_text}")

            return chunks_text
        except Exception as e:
            logger.exception(f"Error retrieving chunks: {e}")
            return f"Error retrieving chunks: {str(e)}"
