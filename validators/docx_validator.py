from werkzeug.datastructures.file_storage import FileStorage
from interfaces.validation_interface import IFileValidator
from config.validation_config import FileValidationConfig, DOCXValidationConfig
from extensions.logger import logger
import zipfile
import docx
import io
from typing import cast, Optional
import re


class DOCXValidator(IFileValidator):
    def __init__(self) -> None:
        """
        Initializes the ImageValidator with configuration from the validation config.

        The configuration is fetched from the config for the 'DOC' type.
        """
        self.config: DOCXValidationConfig = cast(
            DOCXValidationConfig, FileValidationConfig.get_config("DOCX")
        )

    def is_valid(self, uploaded_file: FileStorage) -> bool:
        logger.info("Validating DOCX file")

        file_content = self._get_file_content(uploaded_file)
        if not file_content:
            return False

        if not self._validate_file_size(file_content):
            return False

        io_object = io.BytesIO(file_content)

        if not self._check_zip_file(io_object):
            return False

        io_object.seek(0)

        if not self._check_docx_file(io_object):
            return False

        return True

    @staticmethod
    def _get_file_content(uploaded_file: FileStorage) -> Optional[bytes]:
        try:
            file_content = uploaded_file.read()
            uploaded_file.seek(0)
            return file_content
        except Exception as error:
            logger.warning(f"Error reading file content: {error}")
            return None

    def _check_zip_file(self, io_object: io.BytesIO) -> bool:
        try:
            with zipfile.ZipFile(io_object) as zip_file:
                if "word/vbaProject.bin" in zip_file.namelist():
                    logger.warning("DOCX file contains VBA macros")
                    return False

                if not self._check_embedded_objects(zip_file):
                    return False

            return True
        except zipfile.BadZipFile:
            logger.warning("File is not a valid ZIP archive")
            return False
        except Exception as error:
            logger.warning(f"Error checking ZIP file: {error}")
            return False

    def _check_docx_file(self, io_object: io.BytesIO) -> bool:
        try:
            doc = docx.Document(io_object)
            return self._check_external_links(doc) and self._check_malicious_elements(
                doc
            )
        except docx.opc.exceptions.PackageNotFoundError:
            logger.warning("File is not a valid DOCX document")
            return False
        except Exception as error:
            logger.warning(f"Error processing DOCX file: {error}")
            return False

    @staticmethod
    def _check_external_links(doc: docx.Document) -> bool:
        try:
            # Check for external links
            for rel in doc.part.rels.values():
                if rel.reltype == docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK:
                    logger.warning(
                        "DOCX file contains external links, which could be potentially harmful"
                    )
                    return False
            return True
        except Exception as error:
            logger.warning(f"Error checking for external links: {error}")
            return False

    @staticmethod
    def _check_embedded_objects(zip_file: zipfile.ZipFile) -> bool:
        # Check for embedded objects
        if any("word/embeddings" in name for name in zip_file.namelist()):
            logger.warning(
                "DOCX file contains embedded objects, which could be potentially harmful"
            )
            return False
        return True

    def _check_malicious_elements(self, doc: docx.Document) -> bool:
        # Check document content for potential malicious elements
        full_text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        return self._check_suspicious_keywords(
            full_text
        ) and self._check_script_injection(full_text)

    @staticmethod
    def _check_script_injection(full_text: str) -> bool:
        # Check for potential script injection
        if re.search(r"<script|javascript:|data:>", full_text, re.IGNORECASE):
            logger.warning("DOCX file contains potential script injection")
            return False
        return True

    def _check_suspicious_keywords(self, full_text: str) -> bool:
        suspicious_words = [
            kw for kw in self.config.suspicious_keywords if kw in full_text.lower()
        ]
        if suspicious_words:
            logger.warning(
                f"DOCX file contains suspicious keywords: {suspicious_words}"
            )
            return False
        return True

    def _validate_file_size(self, file_content: bytes) -> bool:
        # Check file size (arbitary limit 10MB)
        if len(file_content) > self.config.max_file_size:
            logger.warning("DOCX file is suspiciously large")
            return False
        return True
