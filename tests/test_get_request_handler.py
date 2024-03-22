import pytest
import unittest.mock as mock
from unittest.mock import patch
from flask import Response
from app import handle_get_request



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
