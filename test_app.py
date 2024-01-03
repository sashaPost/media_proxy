import unittest
from app import app


class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        
    def tearDown(self):
        pass
    
    def test_get_existing_file(self):
        response = self.app.get('/media/images/zystrich1.jpg')
        self.assertEqual(response.status_code, 200)
    
    def test_get_non_existing_file(self):
        response = self.app.get('/media/images/nonexistent.jpg')
        self.assertEqual(response.status_code, 404)
        
    def test_post_upload_file(self):
        data = {'file': (open('zystrich3.jpg', 'rb'), 'zystrich3.jpg')}
        response = self.app.post('/media/images/zystrich3.jpg', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        
    def test_put_update_file(self):
        data = {'file': (open('zystrich_test.jpg', 'rb'), 'zystrich_test.jpg')}
        response = self.app.put('/media/images/zystrich3.jpg', data=data, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        
    def test_delete_existing_file(self):
        response = self.app.delete('/media/images/zystrich3.jpg')
        self.assertEqual(response.status_code, 200)
        
    def test_delete_non_existing_file(self):
        response = self.app.delete('/media/images/nonexistent.jpg')
        self.assertEqual(response.status_code, 404)
        
        
        
if __name__ == "__main__":
    unittest.main()