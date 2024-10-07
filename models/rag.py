from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains.question_answering import load_qa_chain
from dotenv import load_dotenv
import os
from supabase import create_client, Client

load_dotenv()
url: str = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key: str = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)
embeddings = OpenAIEmbeddings()


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
    chain = load_qa_chain(ChatOpenAI(model_name="gpt-3.5-turbo"), chain_type="stuff")
    return chain.invoke({"input_documents": similar_texts, "question": query})[
        "output_text"
    ]
