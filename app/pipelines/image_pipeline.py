from base64 import b64encode
from io import BytesIO
from typing import Tuple

from fastapi import UploadFile
from PIL import Image
from pytesseract import image_to_string, image_to_data, Output

from .base_pipeline import BasePipeline

class ImagePipeline(BasePipeline):
    CONFIDENCE_THRESHOLD = 75               # Minimally 75% confidence
    CHAR_DENSITY_THRESHOLD = 0.00025        # Minimally 0.25 characters per 1000 pixels

    def _is_ocr_sufficient(self, ocr_data: dict, image_text: str, image_size: Tuple[int, int]) -> bool:
        """
        Determines if the OCR results for a given image is sufficient on the basis of confidence scores and character densities.

        Minimum average confidence score = 75
        Minimum characters per 1000 pixels = 0.25

        Args:
            ocr_data (dict): OCR data.
            image_text (str): Extracted text from image.
            image_size (tuple): Size of image.

        Returns:
            bool: Boolean indicating whether OCR result is sufficient.
        """
        # Calculate average confidence
        confidences = [float(conf) for conf in ocr_data['conf'] if conf != '-1']
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        # Calculate character density
        char_count = len(image_text.strip())
        image_area = image_size[0] * image_size[1]
        char_density = char_count / image_area if image_area != 0 else 0

        is_confidence_sufficient = avg_confidence >= self.CONFIDENCE_THRESHOLD
        is_density_sufficient = char_density >= self.CHAR_DENSITY_THRESHOLD

        return is_confidence_sufficient and is_density_sufficient

    def _process_image(self, image_data: bytes) -> str:
        """
        Processes an image for subsequent embedding.

        1. Extract text from image using OCR.
        2. If no text is found, generate an image description using Gemini 2.0 Flash-Lite.

        Args:
            image_data (bytes): Binary content of uploaded image.

        Returns:
            str: String containing the image contents or its description for subsequent embedding.
        """
        im = Image.open(BytesIO(image_data))

        ocr_data = image_to_data(im, output_type=Output.DICT)
        im_text = image_to_string(im)

        if self._is_ocr_sufficient(ocr_data, im_text, im.size):
            return im_text

        image_b64_data = self._encode_pil_image_to_base64(im)

        description = self._describe_image(image_b64_data)
        return description

    def handle_file(self, uploaded_file: UploadFile):
        image_data = self._read_file(uploaded_file)

        try:
            # Process the image to extract its text / generate a description for it
            text = self._process_image(image_data)

            contents, embeddings = self._create_embeddings(text)

            document_entry = self._insert_document()
            document_id = document_entry["document_id"]

            response = self._insert_embeddings(document_id, contents, embeddings)
        except RuntimeError as e:
            self.logger.error(e)
