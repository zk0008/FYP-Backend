from os import remove
from pathlib import PosixPath, WindowsPath
from typing import List

from pymupdf import Document
from pymupdf4llm import to_markdown

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
        texts = []
        for i, page in enumerate(pdf, start=1):
            pixmap = page.get_pixmap()
            im = pixmap.pil_image()

            image_b64_data = self._encode_pil_image_to_base64(im)
            try:
                text = self._describe_image(image_b64_data)
                texts.append(text)
            except RuntimeError as e:
                self.logger.error(f"Error occurred when generating descriptions for page {i}: {e}")
                continue

        return texts

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

    def handle_file(self, filename: str, path: PosixPath | WindowsPath):# uploaded_file: UploadFile):
        """
        Handles the uploaded PDF file.

        1. Extract PDF text using PyMuPDF4LLM for research paper-type documents / generate slide descriptions using vision LLM.
        2. Create embeddings of extracted text / generated description.
        3. Insert document (i.e., the PDF file) and embeddings entries into DB.

        Args:
            filename (str): Original
        """
        

        try:
            pdf = Document(path)
            # pdf = Document(stream=uploaded_file.file.read())        # TODO: Does not successfully run in BackgroundTasks; likely because read() is async

            # Process the PDF to extract its text / generate descriptions for it
            text = self._process_pdf(pdf)                           # TODO: Untested, but likely does not successfully run in BackgroundTasks as well
            self.logger.debug("Successfully processed PDF")

            contents, embeddings = self._create_embeddings(text)
            self.logger.debug("Successfully created embeddings")

            document_entry = self._insert_document(filename)
            document_id = document_entry["document_id"]
            self.logger.debug("Successfully inserted document entry to database")

            response = self._insert_embeddings(document_id, contents, embeddings)
            self.logger.debug("Successfully inserted embeddings entries to database")
        except RuntimeError as e:
            self.logger.exception(e)
        finally:
            try:
                remove(path)
                self.logger.info("Successfully added PDF to knowledge base")
            except Exception as e:
                self.logger.exception(e)