import pytest
from app import *
import os



@pytest.fixture(scope='module')
def client():
    app.config['TESTING'] = True
    app.config['MEDIA_FILES_DEST'] = 'media'
    with app.test_client() as client:
        yield client

@pytest.fixture()
def api_key():
    return os.getenv('API_KEY')
    
@pytest.fixture()
def valid_image_data():
    return b'89 PNG\r\n\x1a\n\x00\x00\x00\rIHDR'

@pytest.fixture()
def invalid_image_data():
    return b'This is not an image file'

@pytest.fixture()
def media_files_destination():
    return app.config['MEDIA_FILES_DEST']
