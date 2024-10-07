from PyPDF2 import PdfReader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from dotenv import load_dotenv
import os
from supabase import create_client, Client

load_dotenv()
url: str = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key: str = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)
embeddings = OpenAIEmbeddings()


def download_pdf(topic: str, file_name: str):
    # Download the PDF file from Supabase storage
    data = supabase.storage.from_("chat-room-documents").download(
        f"{topic}/{file_name}"
    )
    return data


def insert_embedding_into_supabase(text: str, embedding: list, topic: str):
    # Insert the text and its corresponding embedding into Supabase
    supabase.table("document_vectors").insert(
        {"text": text, "embedding": embedding, "topic": topic}
    ).execute()


def embed_document(topic: str, file_name: str):
    raw_text = ""
    pdf_content = download_pdf(topic, file_name)
    with open(file_name, "wb") as f:
        f.write(pdf_content)

    pdfreader = PdfReader(file_name)
    for page in pdfreader.pages:
        content = page.extract_text()
        if content:
            raw_text += content

    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=800,
        chunk_overlap=200,
        length_function=len,
    )
    texts = text_splitter.split_text(raw_text)

    # Insert each text chunk and its embedding into Supabase
    count = 0
    for text in texts:
        count += 1
        embedding = embeddings.embed_query(text)  # Create the embedding for the chunk
        insert_embedding_into_supabase(text, embedding, topic)
        print("Embedding" + str(count))

    # Delete the file after processing
    os.remove(file_name)
    print(f"Document {topic}/{file_name} successfully embedded")
