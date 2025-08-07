from base64 import b64encode
from io import BytesIO
import logging
from pathlib import PosixPath, WindowsPath
from typing import List, Tuple

from fastapi import UploadFile
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PIL import Image
from tiktoken import encoding_for_model

from app.constants import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    EMBEDDING_MODEL_NAME
)
from app.dependencies import get_settings, get_supabase
from app.llms import gemini_2_flash_lite
from .components.parsers import img_desc_parser, img_desc_reparser
from .components.prompts import IMAGE_DESCRIPTION_PROMPT


class BasePipeline:
    MAX_RETRIES = 3


    def __init__(
        self,
        uploader_id: str,
        chatroom_id: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    ):
        self.uploader_id = uploader_id
        self.chatroom_id = chatroom_id

        self.embedding_model = OpenAIEmbeddings(model=EMBEDDING_MODEL_NAME)
        self.encoding = encoding_for_model(EMBEDDING_MODEL_NAME)

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=lambda text: len(self.encoding.encode(text))
        )

        self.supabase = get_supabase()
        self.logger = logging.getLogger(self.__class__.__name__)


    def _invoke_model_with_retry(self, message: HumanMessage) -> AIMessage:
        for attempt in range(self.MAX_RETRIES):
            try:
                response = gemini_2_flash_lite.invoke([message])
                return response
            except Exception as e:
                if attempt < self.MAX_RETRIES - 1:
                    self.logger.warning(f"Model invocation on attempt {attempt + 1} failed. Retrying...", exc_info=True)
                else:
                    raise RuntimeError(e)


    def _encode_pil_image_to_base64(self, pil_image: Image.Image, format: str = "PNG") -> str:
        """
        Encodes an input PIL image into a base64 byte-string in the specified format.

        Args:
            pil_image: PIL image to be encoded.
            format (str): Format to encode the resulting base64 byte-string in. Defaults to "PNG".

        Returns:
            str: Base64 byte-string.
        """
        buffer = BytesIO()
        pil_image.save(buffer, format=format)
        encoded_str = b64encode(buffer.getvalue()).decode("utf-8")
        return encoded_str


    def _describe_image(self, image_b64_data: str, mime_type: str = "image/png") -> str:
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": IMAGE_DESCRIPTION_PROMPT
                },
                {
                    "type": "media",
                    "source_type": "base64",
                    "data": image_b64_data,
                    "mime_type": mime_type
                }
            ]
        )

        try:
            response = self._invoke_model_with_retry(message)
            parsed_content = img_desc_parser.parse(response.content)
            return parsed_content.image_description
        except OutputParserException:
            fixed_content = img_desc_reparser.parse(response.content)
            return fixed_content.image_description
        except Exception as e:
            raise RuntimeError(f"Image description failed with error: {e}")


    def _create_embeddings(self, text: str) -> Tuple[List[str], List[List[float]]]:
        # Split text into chunks for subsequent embedding
        contents = self.text_splitter.split_text(text)

        # Create embeddings for each of the text chunks
        embeddings = self.embedding_model.embed_documents(contents)

        return contents, embeddings


    def _insert_document(self, document_id: str, filename: str) -> dict:
        try:
            response = (
                self.supabase.table("documents")
                .insert({
                    "document_id": document_id,
                    "uploader_id": self.uploader_id,
                    "chatroom_id": self.chatroom_id,
                    "filename": filename
                })
                .execute()
            )
            return response
        except Exception as e:
            raise RuntimeError(f"Document entry insertion failed with error: {e}")

    def _insert_embeddings(self, document_id: str, contents: List[str], embeddings: List[List[float]]) -> dict:
        try:
            payload = [
                {
                    "document_id": document_id,
                    "chunk_index": i,
                    "content": content,
                    "embedding": embedding
                }
                for i, (content, embedding) in enumerate(zip(contents, embeddings))
            ]

            response = (
                self.supabase.table("chunks")
                .insert(payload)
                .execute()
            )

            return response
        except Exception as e:
            raise RuntimeError(f"Chunk entry insertion failed with error: {e}")


    def _upload_file_to_supabase(self, filename: str, path: PosixPath | WindowsPath) -> dict:
        try:
            with open(path, "rb") as f:
                response = (
                    self.supabase.storage
                    .from_("uploaded-documents")  # Name of bucket
                    .upload(
                        file=f,
                        path=f"{self.chatroom_id}/{filename}"
                    )
                )

            return response
        except Exception as e:
            raise RuntimeError(f"File upload to Supabase bucket failed with error: {e}")


    def _notify_chatroom_file_uploaded(self, filename: str, uploader_id: str, chatroom_id: str) -> None:
        """
        Notifies the chatroom that a file has been successfully uploaded.

        Args:
            filename (str): Name of the uploaded file.
            uploader_id (str): ID of the user who uploaded the file.
            chatroom_id (str): ID of the chatroom where the file was uploaded.
        """
        try:
            response = (
                self.supabase.table("users")
                .select("username")
                .eq("user_id", uploader_id)
                .execute()
            )
            username = response.data[0]["username"] if response.data else None
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve username for user_id {uploader_id}: {e}")

        try:
            notify_text = f"Hey {username}, your document '{filename}' has been successfully uploaded and added to my knowledge base. You may now query it."

            settings = get_settings()
            (
                self.supabase.table("messages")
                .insert({
                    "sender_id": settings.GROUPGPT_USER_ID,
                    "chatroom_id": chatroom_id,
                    "content": notify_text,
                })
                .execute()
            )
        except Exception as e:
            raise RuntimeError(f"Failed to notify chatroom {chatroom_id} about file upload: {e}")


    def handle_file(self, document_id: str, filename: str, path: PosixPath | WindowsPath):
        raise NotImplementedError
