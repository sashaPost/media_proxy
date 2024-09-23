import pytest
import unittest.mock as mock
from app import check_api_key


class TestHelperFunctions:
    def test_check_api_key_correct_key(self, client, api_key):
        mock_request = mock.MagicMock()
        mock_request.headers = {"Authorization": api_key}

        @check_api_key
        def test_route():
            return "OK"

        result = client.post("/media/images/test.jpg", headers=mock_request.headers)
        assert result.status_code == 200
        assert result.data == b"OK"

    def test_check_api_key_incorrect_key(self, client):
        mock_request = mock.MagicMock()
        mock_request.headers = {"Authorization": "False API key"}

        @check_api_key
        def test_route():
            return "OK"

        result = client.post("/media/images/test.jpg", headers=mock_request.headers)
        assert result.status_code == 401

    # * fix this later *
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
