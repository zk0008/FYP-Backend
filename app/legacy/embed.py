from PyPDF2 import PdfReader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
from supabase import create_client, Client

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)
embeddings = OpenAIEmbeddings()
llm = ChatOpenAI(model="gpt-4o-mini")


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


def summarize_text(text: str) -> str:
    # Use OpenAI's GPT model to summarize the text
    messages = [
        (
            "system",
            "You are a chatbot meant to summarize PDF text that is uploaded by user, usually for educational purposes. Your job is to summarize it accurately."
            + "This summary will be used as a data source in a LLM for queries the user may have later on. If the summary cannot provide the answer for the user, we will then proceed to open the full PDF.",
        ),
        ("user", f"Please summarize the following PDF text: {text}"),
    ]
    return llm.invoke(messages).content


def insert_summary_into_supabase(summary: str, topic: str, file_name: str):
    # Insert the summarized text into Supabase
    supabase.table("document_summaries").insert(
        {"filepath": f"{topic}/{file_name}", "summary": summary}
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

    # Generate a summary of the entire document
    summary = summarize_text(raw_text)
    insert_summary_into_supabase(summary, topic, file_name)
    print(f"Completed Summarization of {topic}/{file_name}")

    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=4000,
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
        print(f"Document {topic}/{file_name} embedding {count} done")

    supabase.table("chats").insert(
        {
            "topic": topic,
            "username": "AI Chatbot",
            "message": f"Document {file_name} successfully embedded",
        }
    ).execute()
    print(f"Completed embedding of {topic}/{file_name}")

    # Delete the file after processing
    os.remove(file_name)
