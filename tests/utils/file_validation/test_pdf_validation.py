import pytest
from unittest.mock import patch, MagicMock
from utils.file_validation import is_valid_pdf


class TestIsValidPDF:
    @pytest.fixture
    def mock_pdf_reader(self):
        with patch("utils.file_validation.PdfReader") as mock:
            yield mock

    def test_valid_pdf(self, mock_pdf_reader):
        mock_file = MagicMock()
        mock_file.stream.read.return_value = b"%PDF-1.5"

        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample text"

        mock_reader = MagicMock()
        mock_reader.trailer = {"/Root": {}}
        mock_reader.pages = [mock_page]

        mock_pdf_reader.return_value = mock_reader

        assert is_valid_pdf(mock_file) is True

    def test_pdf_with_javascript(self, mock_pdf_reader):
        mock_file = MagicMock()
        mock_file.stream.read.return_value = b"%PDF-1.5"

        mock_reader = MagicMock()
        mock_reader.trailer = {"/Root": {"/EmbeddedFiles": {}}}
        mock_reader.pages = [{}]

        mock_pdf_reader.return_value = mock_reader

        assert is_valid_pdf(mock_file) is False

    def test_pdf_with_suspicious_keywords(self, mock_pdf_reader):
        mock_file = MagicMock()
        mock_file.stream.read.return_value = b"%PDF-1.5"

        mock_reader = MagicMock()
        mock_reader.trailer = {"/Root": {}}
        mock_reader.pages = [MagicMock()]
        mock_reader.pages[0].extract_text.return_value = "eval('malicious code')"

        mock_pdf_reader.return_value = mock_reader

        assert is_valid_pdf(mock_file) is False

    def test_pdf_with_external_links(self, mock_pdf_reader):
        mock_file = MagicMock()
        mock_file.stream.read.return_value = b"%PDF-1.5"

        mock_reader = MagicMock()
        mock_reader.trailer = {"/Root": {}}
        mock_reader.pages = [MagicMock()]
        mock_reader.pages[0].extract_text.return_value = "Visit https://example.com"

        mock_pdf_reader.return_value = mock_reader

        assert is_valid_pdf(mock_file) is False
