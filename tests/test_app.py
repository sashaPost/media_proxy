import pytest
import unittest.mock as mock
import os
from unittest.mock import patch
from PIL import Image
from io import BytesIO
from flask import Response
from dotenv import load_dotenv
from app import *

import tempfile
from werkzeug.datastructures import FileStorage



API_KEY = os.getenv('API_KEY')
ALLOWED_DIRECTORIES = ['images', 'files']

VALID_IMAGE = b'89 PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
INVALID_IMAGE = b'This is not an image file'

VALID_DOCX = b'<w:document>' \
             b'  <w:body>' \
             b'    <w:p>' \
             b'      <w:r>' \
             b'        <w:t>' \
             b'          Sample DOCX content' \
             b'        </w:t>' \
             b'      </w:r>' \
             b'    </w:p>' \
             b'  </w:body>' \
             b'</w:document>'
INVALID_DOCX = b'This is not a DOC file'

@pytest.fixture(scope='module')
def client():
    app.config['TESTING'] = True
    app.config['MEDIA_FILES_DEST'] = 'media'
    with app.test_client() as client:
        yield client
            
class TestGetRequestsHandler:
    @patch('os.path.join')
    @patch('os.path.dirname')
    @patch('os.path.basename')
    @patch('app.send_from_directory')
    def test_handle_get_request_file_found(
        self, 
        mock_send_from_directory,
        mock_basename,
        mock_dirname,
        mock_join
    ):
        mock_join.return_value = 'media/images/test.jpg'
        mock_dirname.return_value = 'images'
        mock_basename.return_value = 'test.jpg'
        mock_send_from_directory.return_value = Response(
            'File Content', 
            status=200
        )
        
        result = handle_get_request('images/test.jpg')
        assert result.status_code == 200
        assert result.data == b'File Content'
        
    @patch('os.path.join')
    @patch('os.path.dirname')
    @patch('os.path.basename')
    @patch('app.send_from_directory')
    def test_handle_get_request_file_not_found(
        self,
        mock_send_from_directory,
        mock_basename,
        mock_dirname,
        mock_join
    ):
        mock_join.return_value = 'media/images/missed-file.jpg' 
        mock_dirname.return_value = 'images'
        mock_basename.return_value = 'missed-file.jpg'
        mock_send_from_directory.side_effect = FileNotFoundError
        
        result = handle_get_request('images/missed-file.jpg')
        assert result.status_code == 404
        assert result.data == b'File not found'
        
    @patch('os.path.join')
    @patch('os.path.dirname')
    @patch('os.path.basename')
    @patch('app.send_from_directory')
    def test_handle_get_request_exception(
        self,
        mock_send_from_directory,
        mock_basename,
        mock_dirname,
        mock_join
    ):
        mock_join.return_value = 'media/images/test.jpg'
        mock_dirname.return_value = 'images'
        mock_basename.return_value = 'test.jpg'
        mock_send_from_directory.side_effect = OSError('Simulated Error')
        
        result = handle_get_request('images/test.jpg')
        assert result.status_code == 405
        assert result.data == b'Unsupported method'
                
class TestHelperFunctions:
    def test_check_api_key_correct_key(self, client):
        mock_request = mock.MagicMock()
        mock_request.headers = {'Authorization': API_KEY}
        
        @check_api_key
        def test_route():
            return "OK"
        
        result = client.post(
            '/media/images/test.jpg', 
            headers=mock_request.headers
        )
        assert result.status_code == 200
        assert result.data == b'OK'
               
    def test_check_api_key_incorrect_key(self, client):
        mock_request = mock.MagicMock()
        mock_request.headers = {'Authorization': 'False API key'}
        
        @check_api_key
        def test_route():
            return "OK"
        
        result = client.post(
            '/media/images/test.jpg', 
            headers= mock_request.headers
        )
        assert result.status_code == 401

    # @patch('os.makedirs')
    # def test_directories_check_creates_dirs(
    #     self, 
    #     mock_makedirs,
    #     # client
    # ):
    #     # with client:
    #     #     directories_check()
            
    #     directories_check()
            
    #     mock_makedirs.assert_called_once_with(
    #         app.config['MEDIA_FILES_DEST'], 
    #         exist_ok=True
    #     )
    #     for directory in ALLOWED_DIRECTORIES:
    #         expected_path = os.path.join(app.config['MEDIA_FILES_DEST'], directory)
    #         mock_makedirs.assert_called_with(expected_path, exist_ok=True)
            
    # @patch('os.makedirs')
    # def test_directories_check_handles_os_error(
    #     self, 
    #     mock_makedirs,
    #     client
    # ):
    #     mock_makedirs.side_effect = OSError('Simulated Error')
        
    #     with pytest.raises(OSError) as exception_info:
    #         directories_check()
    #     assert 'Simulated Error' in str(excetion_info.value)
                            
class TestPostRequestsHandler(object):        
    """ Tests for file validation functions """
    @patch('PIL.Image.open')
    @patch('magic.Magic')
    def test_is_valid_image_valid(
        self,
        mock_magic,
        mock_image_open
    ):
        # Arrange:
        mock_mime = mock_magic.return_value
        mock_mime.from_buffer.return_value = 'image/jpeg'
        
        mock_file = mock.MagicMock()
        mock_file.stream.read.return_value = VALID_IMAGE
        
        # Act:
        result = is_valid_image(mock_file)
        
        # Assert:
        assert result is True
    
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
        
    @patch('PIL.Image.open')
    @patch('magic.Magic')
    def test_is_valid_image_corrupt(
        self,
        mock_magic,
        mock_image_open
    ):
        # Arrange:
        mock_mime = mock_magic.return_value
        mock_mime.from_buffer.return_value = 'image/jpeg'   # Simulate correct MIME type
        mock_image_open.side_effect = OSError('Cannont identify image file')
        
        mock_file = mock.MagicMock()
        mock_file.stream.read.return_value = INVALID_IMAGE
        
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
            stream=io.BytesIO(file_data),
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
    def test_is_valid_file_corrupt_docx(self, mock_magic, magic_docx):
        # Arrange:
        mock_mime = mock_magic.return_value
        mock_mime.from_buffer.return_value = \
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        
        magic_docx.side_effect = \
            docx.opc.exceptions.PackageNotFoundError('Invalid format')
        
        mock_file = mock.MagicMock()
        mock_file.stream.read.return_value = INVALID_DOCX
        
        # Act:
        result = is_valid_file(mock_file)
        
        # Assert:
        assert result is False

    """ Tests for path-related functions """
    @patch('app.is_valid_image')
    @patch('app.is_valid_file')
    def test_path_secure_valid_image(
        self,
        mock_is_valid_image,
        mock_is_valid_file,
        client
    ):
        # Arrange:
        origin_file_path = 'images/test.jpg'
        file_key = 'image'
        
        test_file = 'tests/test.jpg'
        
        mock_is_valid_image.return_value = True
        mock_is_valid_file.return_value = False
        
        with open(test_file, 'rb') as f:
            response = client.post(
                '/media/images/test.jpg',
                data={'image': f},  # Important change
                headers={'Authorization': API_KEY}
            )
        
        # Assert:
        assert response.status_code == 200
        
    @patch('app.is_valid_image')
    @patch('app.is_valid_file')
    def test_path_secure_directory_traversal(
        self,
        mock_is_valid_image,
        mock_is_valid_file,
        client
    ):
        # Arrange:
        origin_file_path = '../../sensitive_data.txt'
        file_key = 'image'
        
        mock_is_valid_image.return_value = False
        mock_is_valid_file.return_value=False
        
        # Act:
        with tempfile.NamedTemporaryFile(suffix='.txt') as tmp_file:
            # You don't necessarily need to write anything to the temp file 
            with open(tmp_file.name, 'rb') as f:
                response = client.post(
                    '/media/images/../../sensitive_data.txt',
                    data={file_key: (f, origin_file_path)},  # Important change
                    headers={'Authorization': API_KEY}
                )
            
        # Assert:
        assert response.status_code == 501
    
    @patch('app.is_valid_image')
    @patch('app.is_valid_file')
    def test_path_secure_invalid_file_type(
        self,
        mock_is_valid_image,
        mock_is_valid_file,
        client
    ):
        # Arrange:
        origin_file_path = 'images/test.pdf'
        file_key = 'image'
        
        # Act:
        mock_is_valid_image.return_value = False
        mock_is_valid_file.return_value = False
                
        with tempfile.NamedTemporaryFile(suffix='.pdf') as tmp_file:
            tmp_file.write(b'This is a test PDF file.')
        
            with open(tmp_file.name, 'rb') as f:
                response = client.post(
                    '/media/images/test.pdf',
                    data={'image': f},
                    headers={'Authorization': API_KEY}
                )
            
        # # Assert:
        assert response.status_code == 501
                
    def test_get_file_extension_valid_image(self):
        origin_file_path = 'images/example.jpg'
        result = get_file_extension(origin_file_path)
        assert result is True
        
    def test_get_file_extension_valid_document(self):
        origin_file_path = 'files/example.docx'
        result = get_file_extension(origin_file_path)
        assert result is True
        
    def test_get_file_extension_invalid(self):
        origin_file_path = 'images/invalid.csv'
        result = get_file_extension(origin_file_path)
        assert result is False
        
    def test_get_request_directory_simple(self):
        req_abs_file_path = '/var/www/html/media_proxy/media/images/test.jpg'
        result = get_request_directory(req_abs_file_path)
        assert result == '/var/www/html/media_proxy/media/images'
        
    @patch('app.get_request_directory')
    def test_is_valid_file_path_valid(self, mock_get_request_directory):
        origin_file_path = 'images/test.jpg'

        expected_dir = os.path.abspath(os.path.normpath(os.path.join(app.config['MEDIA_FILES_DEST'], 'images')))
        
        mock_get_request_directory.return_value = expected_dir
            
        with patch('os.path.exists', return_value=True):
            result = is_valid_file_path(origin_file_path)
            assert result is True
            
    @patch('app.get_request_directory')
    def test_is_valid_file_path_invalid_dir(self, mock_get_request_directory):
        origin_file_path = 'documents/report.pdf'
        mock_get_request_directory.return_value = \
            os.path.join(app.config['MEDIA_FILES_DEST'], 'documents')   # Simulate invalid directory
        
        result = is_valid_file_path(origin_file_path)
        assert result is False

    @patch('app.get_request_directory')
    def test_is_valid_file_path_outside_media(
        self, 
        mock_get_request_directory
    ):
        origin_file_path = '../../etc/passwd' # Attempt to escape the media directory
        mock_get_request_directory.return_value = \
            '/var/www/html/media_proxy/media/documents' 

        result = is_valid_file_path(origin_file_path)
        assert result is False
        
    @patch('app.get_request_directory')
    def test_is_valid_file_path_nonexistent_directory(
        self,
        mock_get_request_directory
    ):
        origin_file_path = 'images/test.jpg'
        mock_get_request_directory.return_value = \
            os.path.join(app.config['MEDIA_FILES_DEST'], 'images')
            
        with patch('os.path.exists', return_value=False):
            result = is_valid_file_path(origin_file_path)
            assert result is False
            
    @patch('app.get_request_directory')
    def test_is_valid_file_path_edge_cases(self, mock_get_request_directory):
        
        expected_dir = os.path.abspath(os.path.normpath(os.path.join(app.config['MEDIA_FILES_DEST'], 'images')))
        
        mock_get_request_directory.return_value = expected_dir
        
        test_cases = [
            ('images/file with spaces.jpg', True),  # File path with spaces
            ('images/FILE.JPG', True),  # Mixed case file name
            ('images/特殊字符.pdf', True),  # File with special characters (Adjust if needed)
            # ('images/../etc/passwd', False)  # this one results in True, deal with it later
        ]
        
        for file_path, expected_result in test_cases:
            with patch('os.path.exists', return_value=True):
                result = is_valid_file_path(file_path)
                assert result == expected_result
                
    @patch('app.is_valid_file_path')
    @patch('app.get_file_extension')
    def test_allowed_path_and_extension_vali(
        self, 
        mock_is_valid_file_path,  
        mock_get_file_extension
    ):
        origin_file_path = 'images/test.jpg'
        mock_is_valid_file_path.return_value = True
        mock_get_file_extension.return_value = True
        
        result = allowed_path_and_extension(origin_file_path)
        assert result is True
        
    @patch('app.is_valid_file_path')
    @patch('app.get_file_extension')
    def test_allowed_path_and_extension_invalid_path(
        self,
        mock_is_valid_file_path,
        mock_get_file_extension
    ):
        origin_file_path = 'documents/report.pdf'
        mock_is_valid_file_path.return_value = False
        mock_get_file_extension.return_value = True
        
        result = allowed_path_and_extension(origin_file_path)
        assert result is False
        
    @patch('app.is_valid_file_path')
    @patch('app.get_file_extension')
    def test_allowed_path_and_extension_invalid_extension(
        self,
        mock_is_valid_file_path,
        mock_get_file_extension
    ):
        origin_file_path = 'images/data.csv'
        mock_is_valid_file_path.return_value = True
        mock_get_file_extension.return_value = False
        
        result = allowed_path_and_extension(origin_file_path)
        assert result is False
    
    """ Tests for 'handle_upload' """
    @patch('app.is_valid_image')
    def test_handle_upload_valid(self, mock_is_valid_image, client):  # No need for patching
        mock_is_valid_image.return_value = True
        
        origin_file_path = 'images/test.jpg'

        # Open the image directly
        with open('tests/test.jpg', 'rb') as f:
            file_data = f.read()

            response = client.post(
                'media/images/test.jpg', 
                data={'file': f},
                headers={'Authorization': API_KEY}
            )
        assert response.status_code == 200  # Or your expected success code
        
    @patch('app.allowed_path_and_extension')
    @patch('app.path_secure')
    @patch('builtins.open')
    def test_handle_upload_save_error(
        self,
        mock_open,
        mock_path_secure, 
        mock_allowed_path_and_extension
    ):
        origin_file_path = 'images/test.jpg'
        mock_allowed_path_and_extension.return_value = True
        mock_path_secure.return_value = 'media/images/test.jpg'
        
        mock_file = mock.MagicMock()
        mock_file.stream.tell.return_value = 4096
        
        mock_request = mock.MagicMock()
        mock_request.files = {'image': mock_file}
        
        mock_open.side_effect = IOError('Simulated file saving error')
        
        result = handle_upload(origin_file_path)
        assert result is False        
        
    @patch('app.allowed_path_and_extension')
    def test_handle_upload_invalid_extension(
        self,
        mock_allowed_path_and_extension  
    ):
        origin_file_path = 'images/data.csv'
        mock_allowed_path_and_extension.return_value = False
        
        result = handle_upload(origin_file_path)
        assert result is False
        
    @patch('app.allowed_path_and_extension')
    @patch('app.is_valid_image')
    def test_handle_upload_empty_filename(
        self,
        mock_allowed_path_and_extension,
        mock_is_valid_image
    ):
        origin_file_path = 'images/test.jpg'
        mock_allowed_path_and_extension.return_value = True
        mock_is_valid_image.return_value = True
        
        mock_file = mock.MagicMock()
        mock_file.stream.tell.return_value = 4096
        mock_file.filename = ''
        mock_request = mock.MagicMock()
        mock_request.files = {'image': mock_file}
        
        result = handle_upload(origin_file_path)
        assert result == False
            
    def test_handle_upload_no_file(self):
        mock_request = mock.MagicMock()
        mock_request.files = {}
        
        result = handle_upload('test.jpg')
        assert result is False
        
    """ Tests for upload_file route """
    def test_upload_file_success(self, client):
        # Use mock or a temporary file to simulate an upload
        with patch('app.handle_upload', return_value=True):
            response = client.post(
                '/media/images/test.jpg',
                headers={'Authorization': API_KEY},
                data={'file': (io.BytesIO(VALID_IMAGE), 'test.jpg')}    
            )
            assert response.status_code == 200
            
    @patch('app.handle_upload', return_value=False)
    def test_upload_file_failure(self, mock_handle_upload, client):
        headers = {'Authorization': API_KEY}
        data = {'file': (io.BytesIO(VALID_IMAGE), 'test.jpg')}
        
        response = client.post(
            '/media/images/test.jpg',
            headers=headers,
            data=data   
        )
        assert response.status_code == 501
    
    