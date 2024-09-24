import pytest
from unittest.mock import patch, MagicMock
from utils.file_validation import is_valid_image


class TestIsValidImage:
    @pytest.fixture
    def mock_magic(self):
        with patch("utils.file_validation.magic.Magic") as mock:
            yield mock

    @pytest.fixture
    def mock_image(self):
        with patch("utils.file_validation.Image.open") as mock:
            yield mock

    def test_is_valid_image(self, mock_magic, mock_image):
        mock_file = MagicMock()
        mock_file.read.return_value = b"\xFF\xD8\xFF"

        mock_magic.return_value.from_buffer.return_value = "image/jpeg"

        mock_img = MagicMock()
        mock_img.format = "JPEG"
        mock_img.size = (100, 100)

        mock_image.return_value.__enter__.return_value = mock_img

        assert is_valid_image(mock_file) is True

    def test_invalid_mime_type(self, mock_magic):
        mock_file = MagicMock()
        mock_file.read.return_value = b"Not an image"

        mock_magic.return_value.from_buffer.return_value = "text/plain"

        assert is_valid_image(mock_file) is False

    def test_large_image(self, mock_magic, mock_image):
        mock_file = MagicMock()
        mock_file.read.return_value = b"\xFF\xD8\xFF"

        mock_magic.return_value.from_buffer.return_value = "image/jpeg"

        mock_img = MagicMock()
        mock_img.format = "JPEG"
        mock_img.size = (10000, 10000)

        mock_image.return_value.__enter__.return_value = mock_img

        assert is_valid_image(mock_file) is False

    def test_jpeg_comment_injection(self, mock_magic, mock_image):
        mock_file = MagicMock()
        mock_file.read.return_value = b"\xFF\xD8\xFF\xFE\x00\x0Ccomment\x00test"

        mock_magic.return_value.from_buffer.return_value = "image/jpeg"

        mock_img = MagicMock()
        mock_img.format = "JPEG"
        mock_img.size = (100, 100)

        mock_image.return_value.__enter__.return_value = mock_img

        assert is_valid_image(mock_file) is False

    def test_png_suspicious_chunk(self, mock_magic, mock_image):
        mock_file = MagicMock()

        # Simulating PNG magic number (first 8 bytes) and a suspicious chunk
        mock_file.read.return_value = (
            b"\x89PNG\r\n\x1a\n"  # PNG signature
            b"\x00\x00\x00\x0b"  # Length of chunk data (11 bytes)
            b"BAD!"  # Chunk type (invalid type)
            b"12345678901"  # Chunk data (11 bytes)
            b"\x00\x00\x00\x00"  # CRC (invalid for simplicity)
        )

        # Mock the MIME type to be image/png
        mock_magic.return_value.from_buffer.return_value = "image/png"

        assert is_valid_image(mock_file) is False
