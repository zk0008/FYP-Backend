import os

from dotenv import load_dotenv
from langchain.chains.question_answering import load_qa_chain
from langchain.schema import Document
from PyPDF2 import PdfReader
from supabase import create_client, Client

from app.llms import gpt_4o_mini

load_dotenv()
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
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

    chain = load_qa_chain(gpt_4o_mini, chain_type="stuff")

    # docs = document_search.similarity_search(query)
    res = chain.invoke(
        {"input_documents": [Document(page_content=raw_text)], "question": query}
    )["output_text"]

    # Cleanup: delete the downloaded PDF files
    for file_name in pdf_files:
        try:
            os.remove(file_name)
        except OSError as e:
            print(f"Error deleting file {file_name}: {e}")

    return res
