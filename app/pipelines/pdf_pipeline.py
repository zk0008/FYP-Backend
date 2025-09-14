import concurrent.futures
from os import remove
from pathlib import PosixPath, WindowsPath
import re
from typing import Optional, List, Tuple

import pymupdf
from pymupdf4llm import to_markdown

from app.llms import google_client
from app.prompts import SLIDE_EXTRACTION_PROMPT

from .base_pipeline import BasePipeline


class PdfPipeline(BasePipeline):
    CHAR_DENSITY_THRESHOLD_PER_SQPT = 0.004


    def _get_avg_char_density(self, pdf: pymupdf.Document) -> float:
        """
        Gets the average character density in characters per square point across all pages of a PDF document.

        Args:
            pdf (Document): Document object of the input PDF document.

        Returns:
            float: Average character density in characters per square point.
        """
        char_densities = []
        for page in pdf:
            area = page.mediabox.width * page.mediabox.height
            text = page.get_text() or ""
            char_density = len(text) / area if area else 0
            char_densities.append(char_density)

        avg_char_density = sum(char_densities) / len(pdf) if len(pdf) != 0 else 0

        return avg_char_density


    def _is_slide(self, filepath: str) -> bool:
        """
        Determines if the input document is a slide deck-type or a paper-type PDF.

        Args:
            filepath (str): Path to input PDF.

        Returns:
            bool: Boolean indicating if the input PDF document is a slide deck-type PDF.
        """
        pdf = pymupdf.open(filepath)
        avg_char_density = self._get_avg_char_density(pdf)
        return avg_char_density < self.CHAR_DENSITY_THRESHOLD_PER_SQPT


    def _replace_images_with_descriptions(self, markdown_content: str, max_workers: int = 5) -> str:
        """
        Replaces base64 encodings of embedded images with an LLM-generated image description.

        Args:
            markdown_content (str): Extracted contents in Markdown containing the embedded images.
            max_workers (int): Defaults to 5. Maximum number of workers to generate image descriptions in parallel.

        Returns:
            str: Extracted contents in Markdown with base64 encodings of embedded images being replaced with their respective descriptions.
        """
        # First step: Extract all base64 encodings of embedded images
        pattern = r"!\[\]\(data:(image/[^;]+);base64,([A-Za-z0-9+/=\s]+)\)"
        matches = re.findall(pattern, markdown_content)

        if not matches:
            return markdown_content

        # Second step: Generate descriptions for every image
        image_data = [(i, mime, b64_data) for i, (mime, b64_data) in enumerate(matches)]
        descriptions = [None] * len(image_data) # Pre-allocated to maintain order

        def process_single_image(image_data: Tuple[int, str, str]) -> Tuple[int, Optional[str]]:
            """
            """
            index, mime_type, image_b64_data = image_data
            try:
                description = self._describe_image(image_b64_data=image_b64_data, mime_type=mime_type)
                return index, description
            except Exception as e:
                self.logger.exception(e)
                return index, None

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(process_single_image, data): data[0] for data in image_data
            }

            for future in concurrent.futures.as_completed(future_to_index):
                index, description = future.result()
                descriptions[index] = description

        # Third step: Replace base64 encodings with respective descriptions
        iter_matches = list(re.finditer(pattern, markdown_content))

        result = markdown_content
        for match, description in zip(reversed(iter_matches), reversed(descriptions)):
            start, end = match.span()
            replacement = f"> Image Description: {description}" if description else "> Image Description Unavailable"
            result = result[:start] + replacement + result[end:]

        return result


    def _extract_from_paper(self, filepath: str) -> str:
        """
        Extracts all content from a paper-type PDF in Markdown format and generating descriptions for all embedded images using a vision LLM.

        Args:
            filepath (str): Path to input PDF.

        Returns:
            str: String containing the extracted text and image descriptions in Markdown format.
        """
        try:
            text = to_markdown(filepath, embed_images=True)
            replaced_text = self._replace_images_with_descriptions(text)
            return replaced_text
        except Exception as e:
            raise RuntimeError(f"Error occurred when extracting text from paper-type {filepath}: {e}")


    def _extract_from_slide(self, filepath: str) -> str:
        """
        Extracts all content from a slide deck-type PDF in Markdown format using a vision LLM.

        Args:
            filepath (str): Path to input PDF.

        Returns:
            str: String containing the extracted content from the PDF.
        """
        try:
            pdf = google_client.files.upload(file=filepath)
            response = google_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[pdf, "\n\n", SLIDE_EXTRACTION_PROMPT]
            )
            google_client.files.delete(name=pdf.name)
            return response.text
        except Exception as e:
            raise RuntimeError(f"Error occurred when extracting text from slide deck-type {filepath}: {e}")


    def _process_pdf(self, filepath: str) -> List[str] | str:
        """
        Process a PDF document for subsequent embedding.

        1. Evaluate PDF to determine if it is paper-type or slide deck-type.
        2.1. If paper-type, extract all text in Markdown format for subsequent embedding.
        2.2. If slide deck-type, generate descriptions for every slide using Gemini 2.0 Flash-Lite.

        Args:
            pdf (Document): Document object of the input document.

        Returns:
            str | List[str]: List of strings that contain descriptions for every slide for slide deck-type documents, or single string containing extracted text in Markdown format for paper-type documents.
        """
        return self._extract_from_slide(filepath) if self._is_slide(filepath) else self._extract_from_paper(filepath)


    def handle_document(self, document_id: str, filename: str, path: PosixPath | WindowsPath):
        """
        Handles the uploaded PDF document.

        1. Extract all content from uploaded PDF.
        2. Create embeddings of the extracted content.
        3. Insert document (i.e., the PDF file) and embeddings entries into the database (DB).
        4. Notifies the chatroom that the document has been successfully uploaded.

        Args:
            document_id (str): UUID v4 of the document entry in the DB.
            filename (str): Name of uploaded PDF document.
            path (PosixPath | WindowsPath): Path to uploaded PDF document. Has the format: <document_id>.pdf
        """
        try:
            # Process the PDF to extract its text / generate descriptions for it
            text = self._extract_from_slide(path) if self._is_slide(path) else self._extract_from_paper(path)

            contents, embeddings = self._create_embeddings(text)

            self._insert_document(document_id, filename)

            self._insert_embeddings(document_id, contents, embeddings)

            self._upload_document_to_supabase(document_id, path)

            self._notify_chatroom_document_uploaded(
                filename=filename,
                uploader_id=self.uploader_id,
                chatroom_id=self.chatroom_id
            )

            remove(path)  # Delete file from local storage after processing

            self.logger.info("Successfully uploaded document to knowledge base.")
        except Exception as e:
            self.logger.exception(f"Error occurred when extracting text from {filename}: {e}")
