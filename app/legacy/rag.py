import os

from dotenv import load_dotenv
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain.chains.question_answering import load_qa_chain
from supabase import create_client, Client

from app.constants import EMBEDDING_MODEL_NAME
from app.llms import gpt_4o_mini

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)
embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL_NAME)


def get_rag_answer(topic: str, query: str):
    # Get the embedding for the query
    query_embedding = embeddings.embed_query(query)

    # Query the Supabase vector table for nearest neighbors
    response = supabase.rpc(
        "get_similar_embeddings",
        {"query_embedding": query_embedding, "query_topic": topic},
    ).execute()

    # Extract the texts from the response
    similar_texts = [Document(page_content=record["text"]) for record in response.data]

    if not similar_texts:
        return "No relevant documents found."

    print(f"Chunks found for query: {len(similar_texts)}")
    # Use the similar texts for question answering
    chain = load_qa_chain(gpt_4o_mini, chain_type="stuff")

    return chain.invoke(
        {
            "input_documents": similar_texts,
            "question": "The following documents are chunks of text fetched from a RAG langchain. You are the last step of the chain, give an accurate answer to the following query using the provided context: "
            + query
            + "If the context is not enough, respond with this fixed template: I do not have enough information to accurately answer that based on current documents.",
        }
    )["output_text"]
