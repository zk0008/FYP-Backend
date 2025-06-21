import concurrent.futures
from os import remove
from pathlib import PosixPath, WindowsPath
from typing import List

from pymupdf import Document
from pymupdf4llm import to_markdown

from app.constants import MAX_WORKERS

from .base_pipeline import BasePipeline

class PdfPipeline(BasePipeline):
    CHAR_DENSITY_THRESHOLD_PER_SQPT = 0.004

    def _get_avg_char_density(self, pdf: Document) -> float:
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

    def _is_slide(self, pdf: Document) -> bool:
        """
        Determines if the input PDF document is a slide deck or a research paper.

        Args:
            pdf (Document): Document object of the input PDF document.

        Returns:
            bool: Boolean indicating if the input PDF document is a slide deck.
        """
        avg_char_density = self._get_avg_char_density(pdf)
        return avg_char_density < self.CHAR_DENSITY_THRESHOLD_PER_SQPT

    def _process_paper(self, pdf: Document) -> str:
        """
        Processes a research paper by extracting text in Markdown format.

        Args:
            pdf (Document): Document object of the input PDF document.

        Returns:
            str: String containing the extracted text in Markdown format.
        """
        text = to_markdown(pdf)
        return text

    def _process_slide(self, pdf: Document) -> List[str]:
        """
        Processes a slide deck by generating descriptions for every individual slide's contents.

        Args:
            pdf (Document): Document object of the input document.

        Returns:
            List[str]: List of strings containing the descriptions of every page.
        """
        def process_single_page(page_data):
            page, page_num = page_data
            try:
                pixmap = page.get_pixmap()
                im = pixmap.pil_image()
                image_b64_data = self._encode_pil_image_to_base64(im)
                text = self._describe_image(image_b64_data)
                return page_num, text
            except RuntimeError as e:
                self.logger.error(f"Error occurred when generating descriptions for page {page_num}: {e}")
                return page_num, None
        
        # Prepare page data with page numbers
        page_data = [(page, i) for i, page in enumerate(pdf, start=1)]
        
        texts = [None] * len(page_data)  # Pre-allocated to maintain order
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_page = {executor.submit(process_single_page, data): data for data in page_data}

            for future in concurrent.futures.as_completed(future_to_page):
                page_num, result = future.result()
                if result is not None:
                    texts[page_num - 1] = result

        # Filter out failed pages (None values)
        return [text for text in texts if text is not None]

    def _process_pdf(self, pdf: Document) -> List[str] | str:
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
        return self._process_slide(pdf) if self._is_slide(pdf) else self._process_paper(pdf)

    def handle_file(self, document_id: str, filename: str, path: PosixPath | WindowsPath):
        """
        Handles the uploaded PDF file.

        1. Extract PDF text using PyMuPDF4LLM for research paper-type documents / generate slide descriptions using vision LLM.
        2. Create embeddings of extracted text / generated description.
        3. Insert document (i.e., the PDF file) and embeddings entries into the database (DB).

        Args:
            document_id (str): UUID v4 of the document entry in the DB.
            filename (str): Name of uploaded PDF file.
            path (PosixPath | WindowsPath): Path to uploaded PDF file.
        """
        try:
            pdf = Document(path)

            # Process the PDF to extract its text / generate descriptions for it
            text = self._process_pdf(pdf)
            self.logger.debug("Successfully processed PDF")

            contents, embeddings = self._create_embeddings(text)
            self.logger.debug("Successfully created embeddings")

            self._insert_document(document_id, filename)
            self.logger.debug("Successfully inserted document entry to database")

            self._insert_embeddings(document_id, contents, embeddings)
            self.logger.debug("Successfully inserted embeddings entries to database")

            self._upload_file_to_supabase(filename, path)
            self.logger.debug("Successfully uploaded file to Supabase bucket")
        except RuntimeError as e:
            self.logger.exception(e)
        finally:
            try:
                remove(path)
                self.logger.info("Successfully added PDF to knowledge base")
            except Exception as e:
                self.logger.exception(e)