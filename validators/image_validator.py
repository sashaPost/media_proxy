from typing import Optional, cast
from config.validation_config import FileValidationConfig, ImageValidationConfig
from interfaces.validation_interface import IFileValidator
from werkzeug.datastructures.file_storage import FileStorage
from extensions.logger import logger
import magic
from PIL import Image
import io
import struct


class ImageValidator(IFileValidator):
    def __init__(self) -> None:
        """
        Initializes the ImageValidator with configuration from the validation config.

        The configuration is fetched from the config for the 'IMAGE' type.
        """
        self.config: ImageValidationConfig = cast(
            ImageValidationConfig, FileValidationConfig.get_config("IMAGE")
        )

    def is_valid(self, uploaded_file: FileStorage) -> bool:
        """
        Validate the uploaded image file by checking its content, MIME type, dimensions,
        and format-specific vulnerabilities.

        Args:
            uploaded_file (FileStorage): The uploaded file object from the request.

        Returns:
            bool: True if the file is valid, False otherwise.
        """
        logger.info("Validating Image file")

        try:
            file_content = self._read_file_content(uploaded_file)
            if not file_content:
                return False

            mime_type = self._check_mime_type(file_content)
            if not mime_type or not mime_type.startswith("image/"):
                return False
            logger.info(f"Detected MIME type: {mime_type}")

            return self._verify_image_content(file_content)
        except Exception as error:
            logger.warning(f"Failed to validate image: {error}")
            return False

    @staticmethod
    def _read_file_content(uploaded_file: FileStorage) -> Optional[bytes]:
        """
        Reads the content of the uploaded file into a bytes object.

        Args:
            uploaded_file (FileStorage): The uploaded file object from the request.

        Returns:
            Optional[bytes]: The file content as bytes, or None if the file could not be read.
        """
        try:
            file_content = uploaded_file.read()
            uploaded_file.seek(0)
            return file_content
        except Exception as e:
            logger.warning(f"Error reading PDF: {e}")
            return None

    @staticmethod
    def _check_mime_type(file_content: bytes) -> Optional[str]:
        # Check the MIME type using python-magic
        """
        Checks the MIME type of the uploaded file content using python-magic.

        Args:
            file_content (bytes): The uploaded file content as bytes.

        Returns:
            str: The detected MIME type, or None if the MIME type could not be determined.

        Raises:
            Exception: If an error occurs while checking the MIME type.
        """
        try:
            mime = magic.Magic(mime=True)
            return mime.from_buffer(file_content)
        except Exception as e:
            logger.warning(f"Error checking file type: {e}")
            return None

    def _verify_image_content(self, file_content: bytes) -> bool:
        """
        Verifies the image content, checking format, dimensions, and vulnerabilities.

        Args:
            file_content (bytes): The uploaded file content as bytes.

        Returns:
            bool: True if the image is valid, False otherwise.

        Raises:
            Exception: If an error occurs while verifying the image.
        """
        try:
            # Open and verify the image using Pillow:
            with Image.open(io.BytesIO(file_content)) as img:
                img.verify()
                logger.info(
                    f"Image format: {img.format}, Size: {img.size}, Mode: "
                    f"{img.mode}"
                )

                if not self._check_image_dimensions(img):
                    return False

                if not self._check_format_specific_vulnerabilities(img, file_content):
                    return False
        except Exception as e:
            logger.warning(f"Error verifying image: {e}")
            return False
        return True

    def _check_image_dimensions(self, img: Image.Image) -> bool:
        """
        Checks the dimensions of the image against the maximum allowed dimensions.

        Args:
            img (Image.Image): The Pillow image object.

        Returns:
            bool: True if the image dimensions are valid, False otherwise.
        """
        if (
            img.width > self.config.max_dimensions[0]
            or img.height > self.config.max_dimensions[1]
        ):
            # if img.size[0] > self.config.max_dimensions[0] or img.size[1] > self.config.max_dimensions[1]:
            logger.warning(f"Image dimensions are suspiciously large: {img.size}")
            return False
        return True

    def _check_format_specific_vulnerabilities(
        self, img: Image.Image, file_content: bytes
    ) -> bool:
        """
        Checks for format-specific vulnerabilities in the image, such as JPEG comment injection, PNG chunk injection, or GIF polyglot attacks.

        Args:
            img (Image.Image): The Pillow image object.
            file_content (bytes): The uploaded file content as bytes.

        Returns:
            bool: True if the image is free of format-specific vulnerabilities, False otherwise.
        """
        match img.format:
            case "JPEG":
                return self._check_jpeg_vulnerabilities(file_content)
            case "PNG":
                return self._check_png_vulnerabilities(file_content)
            case "GIF":
                return self._check_gif_vulnerabilities(file_content)
            case _:
                logger.warning(f"Unsupported image format: {img.format}")
                return False

    @staticmethod
    def _check_jpeg_vulnerabilities(file_content: bytes) -> bool:
        """
        Checks for JPEG comment injection vulnerabilities in the image.

        Args:
            file_content (bytes): The uploaded file content as bytes.

        Returns:
            bool: True if the image is free of JPEG comment injection vulnerabilities, False otherwise.
        """
        if b"comment" in file_content.lower():
            logger.warning("Potential JPEG comment injection detected")
            return False
        return True

    def _check_png_vulnerabilities(self, file_content: bytes) -> bool:
        """
        Checks for suspicious PNG chunks in the image that could be used for
        malicious purposes.

        Args:
            file_content (bytes): The uploaded file content as bytes.

        Returns:
            bool: True if the image is free of suspicious PNG chunks, False otherwise.
        """
        offset = 8
        while offset < len(file_content):
            chunk_length, chunk_type = struct.unpack(
                ">I4s", file_content[offset : offset + 8]
            )
            if chunk_type in [b"IEND", b"IHDR"]:
                break
            if chunk_type not in self.config.allowed_png_chunks:
                logger.warning(f"Suspicious PNG chunk detected: {chunk_type}")
                return False
            offset += chunk_length + 12
        return True

    @staticmethod
    def _check_gif_vulnerabilities(file_content: bytes) -> bool:
        """
        Checks for GIF polyglot vulnerabilities in the image.

        GIF polyglot attacks involve embedding malicious HTML or JavaScript code within a GIF image.
        This method checks if the image contains any suspicious tags, such as <script> or <svg>.
        If any such tags are found, the method returns False, indicating that the image is potentially malicious.

        Args:
            file_content (bytes): The uploaded file content as bytes.

        Returns:
            bool: True if the image is free of GIF polyglot vulnerabilities, False otherwise.
        """
        if b"<script" in file_content or b"<svg" in file_content:
            logger.warning("Potential GIF polyglot detected")
            return False
        return True
