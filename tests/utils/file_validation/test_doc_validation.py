import pytest
from unittest.mock import patch, MagicMock
from utils.file_validation import is_valid_doc
import io
from werkzeug.datastructures import FileStorage


class TestIsValidDOC:
    @pytest.fixture
    def mock_tempfile(self):
        with patch("utils.file_validation.tempfile.NamedTemporaryFile") as mock:
            yield mock

    @pytest.fixture
    def mock_olefile(self):
        with patch("utils.file_validation.olefile.OleFileIO") as mock:
            yield mock

    def test_valid_doc(self, mock_tempfile, mock_olefile):
        # Create a BytesIO object with the file content
        file_content = (
            b"\xD0\xCF\x11\xE0" + b"\x00" * 512
        )  # Add some padding to simulate a larger file
        file_stream = io.BytesIO(file_content)

        # Create a FileStorage object
        mock_file = FileStorage(
            stream=file_stream,
            filename="test.doc",
            content_type="application/msword",
        )

        # Set up the mock OleFileIO object
        mock_ole = MagicMock()
        mock_ole.exists.side_effect = lambda x: x in ["WordDocument", "\\1Table"]
        mock_ole.openstream.return_value.read.return_value = b"Some content"
        mock_olefile.return_value.__enter__.return_value = mock_ole

        # Set up the mock NamedTemporaryFile
        mock_temp_file = MagicMock()
        mock_temp_file.name = "temp_test.doc"
        mock_tempfile.return_value.__enter__.return_value = mock_temp_file

        # Mock os.path.getsize to return a valid file size
        with patch("os.path.getsize", return_value=len(file_content)):
            result = is_valid_doc(mock_file)

        assert result is True

        # Verify that the temp file was written to
        mock_temp_file.write.assert_called()

        # Verify that OleFileIO was called with the temp file name
        mock_olefile.assert_called_with(mock_temp_file.name)

    def test_invalid_doc(self, mock_tempfile, mock_olefile):
        mock_file = MagicMock()
        mock_file.stream.read.return_value = b"Not a DOC file"

        mock_ole = MagicMock()
        mock_ole.exists.return_value = False

        mock_olefile.return_value = mock_ole

        assert is_valid_doc(mock_file) is False

    def test_doc_with_external_links(self, mock_tempfile, mock_olefile):
        mock_file = MagicMock()
        mock_file.stream.read.return_value = b"\xD0\xCF\x11\xE0"

        mock_ole = MagicMock()
        mock_ole.exists.side_effect = lambda x: x in ["WordDocument", "\\1Table"]
        mock_ole.openstream.return_value.read.return_value = b"HTTP://example.com"

        mock_olefile.return_value = mock_ole

        assert is_valid_doc(mock_file) is False

    def test_doc_with_embedded_objects(self, mock_tempfile, mock_olefile):
        mock_file = MagicMock()
        mock_file.stream.read.return_value = b"\xD0\xCF\x11\xE0"

        mock_ole = MagicMock()
        mock_ole.exists.side_effect = lambda x: x in ["WordDocument", "ObjectPool"]

        mock_olefile.return_value = mock_ole

        assert is_valid_doc(mock_file) is False

    def test_doc_with_script_injection(self, mock_tempfile, mock_olefile):
        mock_file = MagicMock()
        mock_file.stream.read.return_value = b"\xD0\xCF\x11\xE0"

        mock_ole = MagicMock()
        mock_ole.exists.side_effect = lambda x: x in "WordDocument"
        mock_ole.openstream.return_value.read.return_value = (
            b'<script>alert("XSS")</script>'
        )

        mock_olefile.return_value = mock_ole

        assert is_valid_doc(mock_file) is False

    def test_doc_with_suspicious_keywords(self, mock_tempfile, mock_olefile):
        mock_file = MagicMock()
        mock_file.stream.read.return_value = b"\xD0\xCF\x11\xE0"

        mock_ole = MagicMock()
        mock_ole.exists.side_effect = lambda x: x == "WordDocument"
        mock_ole.openstream.return_value.read.return_value = b'exec("malicious code")'

        mock_olefile.return_value = mock_ole

        assert is_valid_doc(mock_file) is False

    def test_large_doc(self, mock_tempfile, mock_olefile):
        mock_file = MagicMock()
        mock_file.stream.read.return_value = b"\xD0\xCF\x11\xE0"

        mock_temp = MagicMock()
        mock_temp.name = "large_file.doc"

        mock_tempfile.return_value.__enter__.return_value = mock_temp
        mock_olefile.return_value.exists.return_value = True

        with patch(
            "utils.file_validation.os.path.getsize", return_value=11 * 1024 * 1024
        ):
            assert is_valid_doc(mock_file) is False
