import pytest
from unittest.mock import patch
import unittest.mock as mock
from werkzeug.datastructures import FileStorage
from io import BytesIO
import docx
from app import is_valid_image, is_valid_file



class TestFileValidationFunctions():        
    """ Tests for file validation functions """
    @patch('PIL.Image.open')
    @patch('magic.Magic')
    def test_is_valid_image_valid(
        self,
        mock_magic,
        mock_image_open,
        valid_image_data
    ):
        # Arrange:
        mock_mime = mock_magic.return_value
        mock_mime.from_buffer.return_value = 'image/jpeg'
        
        mock_file = mock.MagicMock()
        mock_file.stream.read.return_value = valid_image_data
        
        # Act:
        result = is_valid_image(mock_file)
        
        # Assert:
        assert result is True
    
        
    @patch('PIL.Image.open')
    @patch('magic.Magic')
    def test_is_valid_image_corrupt(
        self,
        mock_magic,
        mock_image_open,
        invalid_image_data
    ):
        # Arrange:
        mock_mime = mock_magic.return_value
        mock_mime.from_buffer.return_value = 'image/jpeg'   # Simulate correct MIME type
        mock_image_open.side_effect = OSError('Cannont identify image file')
        
        mock_file = mock.MagicMock()
        mock_file.stream.read.return_value = invalid_image_data
        
        # Act:
        result = is_valid_image(mock_file)
        
        # Assert:
        assert result is False
        
    @patch('docx.Document')
    @patch('magic.Magic')
    def test_is_valid_file_valid(self, mock_magic, magic_docx):
        # Arrange:
        mock_mime = mock_magic.return_value
        mock_mime.from_buffer.return_value = \
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        
        file_path = 'tests/example1.docx'
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
            
        mock_file = FileStorage(
            stream=BytesIO(file_data),
            filename='example1.docx'
        )
            
        # Act:
        result = is_valid_file(mock_file)
        
        # Assert:
        assert result is True
           
    @patch('docx.Document')
    @patch('magic.Magic')
    def test_is_valid_file_invalid_mime_type(self, mock_magic, magic_docx):
        # Arrange:
        mock_mime = mock_magic.return_value
        mock_mime.from_buffer.return_value = 'text/plain'   # Incorrect MIME type
        
        mock_file = mock.MagicMock()
        mock_file.stream.read.return_value = b'This is not a word document'
        
        # Act:
        result = is_valid_file(mock_file)
        
        # Assert:
        assert result is False
        
    @patch('docx.Document')
    @patch('magic.Magic')
    def test_is_valid_file_corrupt_docx(
        self, 
        mock_magic, 
        magic_docx, 
        invalid_image_data
    ):
        # Arrange:
        mock_mime = mock_magic.return_value
        mock_mime.from_buffer.return_value = \
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        
        magic_docx.side_effect = \
            docx.opc.exceptions.PackageNotFoundError('Invalid format')
        
        mock_file = mock.MagicMock()
        mock_file.stream.read.return_value = invalid_image_data
        
        # Act:
        result = is_valid_file(mock_file)
        
        # Assert:
        assert result is False



    # * fix this later *
    # @patch('PIL.Image.open')
    # @patch('magic.Magic')
    # def test_is_valid_image_invalid_text_file(
    #     self,
    #     mock_magic,
    #     mock_image_open
    # ):
    #     # Arrange:
    #     mock_mime = mock_magic.return_value
    #     mock_mime.from_buffer.return_value = 'text/plain'
    #     mock_file = mock.MagicMock()
    #     mock_file.stream.read.return_value = b'This is not an image'
        
    #     # Act:
    #     result = is_valid_image(mock_file)
        
    #     # Assert:
    #     assert result is False
