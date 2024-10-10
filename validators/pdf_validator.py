from werkzeug.datastructures.file_storage import FileStorage
from interfaces.validation_interface import IFileValidator
from extensions.logger import logger
import io
from pypdf import PdfReader
import re
from config.validation_config import FileValidationConfig, PDFValidationConfig
from typing import Optional, cast


class PDFValidator(IFileValidator):
    def __init__(self) -> None:
        """
        Initializes the PDFValidator with configuration.
        """
        self.config: PDFValidationConfig = cast(
            PDFValidationConfig, FileValidationConfig.get_config("PDF")
        )

    def is_valid(self, uploaded_file: FileStorage) -> bool:
        """
        Validates if the uploaded file is a valid PDF.

        Args:
            uploaded_file (FileStorage): The uploaded file object to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        logger.info("Validating PDF file")

        try:
            with self._get_pdf_reader(uploaded_file) as reader:
                return all(
                    [
                        self._check_file_size(uploaded_file),
                        self._check_for_javascript(reader),
                        self._check_for_embedded_files(reader),
                        self._check_for_suspicious_keywords(reader),
                        self._check_for_external_links(reader),
                    ]
                )
        except Exception as e:
            logger.warning(f"PDF file validation failed: {e}")
            return False
        finally:
            # Reset stream after processing
            uploaded_file.stream.seek(0)

    @staticmethod
    def _get_pdf_reader(uploaded_file: FileStorage) -> Optional[PdfReader]:
        """
        Creates a PdfReader object from the uploaded file.

        Args:
            uploaded_file (FileStorage): The uploaded file object.

        Returns:
            PdfReader: PdfReader instance for processing.
        """
        try:
            uploaded_file.stream.seek(0)
            pdf_content = uploaded_file.stream.read()
            return PdfReader(io.BytesIO(pdf_content))
        except Exception as e:
            logger.warning(f"Error reading PDF: {e}")
            return None

    def _check_file_size(self, uploaded_file: FileStorage) -> bool:
        """
        Checks if the uploaded PDF exceeds the maximum allowed file size.

        Args:
            uploaded_file (FileStorage): The uploaded file object.

        Returns:
            bool: True if the file size is valid, False if too large.
        """
        if uploaded_file.content_length > self.config.max_file_size:
            logger.warning(
                f"PDF file exceeds maximum size of {self.config.max_file_size} bytes"
            )
            return False
        return True

    @staticmethod
    def _check_for_javascript(reader: PdfReader) -> bool:
        """
        Checks if the PDF contains JavaScript code.

        Args:
            reader (PdfReader): The PDF reader object.

        Returns:
            bool: True if no JavaScript is found, False otherwise.
        """
        for page in reader.pages:
            if "/JS" in page or "/JavaScript" in page:
                logger.warning(
                    "PDF contains JavaScript, which could be potentially harmful."
                )
                return False
            return True

    @staticmethod
    def _check_for_embedded_files(reader: PdfReader) -> bool:
        """
        Checks if the PDF contains embedded files.

        Args:
            reader (PdfReader): The PDF reader object.

        Returns:
            bool: True if no embedded files are found, False otherwise.
        """
        if "/EmbeddedFiles" in reader.trailer["/Root"]:
            logger.warning(
                "PDF contains Embedded Files, which could potentially harmful."
            )
            return False
        return True

    def _check_for_suspicious_keywords(self, reader: PdfReader) -> bool:
        """
        Checks if the PDF contains suspicious keywords based on the configuration.

        Args:
            reader (PdfReader): The PDF reader object.

        Returns:
            bool: True if no suspicious keywords are found, False otherwise.
        """
        pdf_text = "".join(
            page.extract_text() for page in reader.pages if page.extract_text()
        )
        found_keywords = [
            kw for kw in self.config.suspicious_keywords if kw in pdf_text
        ]
        if found_keywords:
            logger.warning(f"PDF file contain suspicious keywords: {found_keywords}")
            return False
        return True

    @staticmethod
    def _check_for_external_links(reader: PdfReader) -> bool:

        """
        Checks if the PDF contains external links.

        Args:
            reader (PdfReader): The PDF reader object.

        Returns:
            bool: True if no external links are found, False otherwise.
        """
        pdf_text = "".join(page.extract_text().lower() for page in reader.pages)
        url_pattern = re.compile(r"https?://\S+|www\.\S+")
        if url_pattern.search(pdf_text):
            logger.warning(
                f"PDF contains external links, which could lead to potentially harmful content."
            )
            return False
        return True
