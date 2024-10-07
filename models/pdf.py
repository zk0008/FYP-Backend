from PyPDF2 import PdfReader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from typing_extensions import Concatenate
from dotenv import load_dotenv
import os
from supabase import create_client, Client

load_dotenv()
url: str = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key: str = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
supabase: Client = create_client(url, key)


def get_pdf_files_from_bucket(topic: str):
    # List files in the specified Supabase storage bucket
    data = supabase.storage.from_("chat-room-documents").list(path=topic)
    return [file["name"] for file in data]


def download_pdf(topic: str, file_name: str):
    # Download the PDF file from Supabase storage
    data = supabase.storage.from_("chat-room-documents").download(
        f"{topic}/{file_name}"
    )
    return data


def get_pdf_answer(topic: str, query: str):
    pdf_files = get_pdf_files_from_bucket(topic)
    if len(pdf_files) == 0:
        return "No documents to query, please upload to get started"

    # read text from pdf
    raw_text = ""
    for file_name in pdf_files:
        pdf_content = download_pdf(topic, file_name)
        # Ensure to read the content in binary mode
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

    embeddings = OpenAIEmbeddings()
    document_search = FAISS.from_texts(texts, embeddings)
    chain = load_qa_chain(ChatOpenAI(model_name="gpt-3.5-turbo"), chain_type="stuff")

    docs = document_search.similarity_search(query)
    return chain.invoke({"input_documents": docs, "question": query})["output_text"]
