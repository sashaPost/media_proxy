import unittest
from app import app
import os



class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        
    def tearDown(self):
        pass
    
    def perform_test(self, method, endpoint, data=None, headers=None):
        """
        Helper function to perform a test for a given HTTP method and endpoint.
        """
        print("Method inside 'perform_test':", method)
        
        if data:
            response = getattr(self.app, method.lower())(
                endpoint, 
                data=data, 
                headers=headers,
                content_type='multipart/form-data',
                buffered=True,
            )
        else:
            response = getattr(self.app, method.lower())(endpoint, data=data, headers=headers)
        return response
    
    def create_test_method(self, method, endpoint, data=None, headers=None):
        """
        Helper function to dynamically create a test method for a given HTTP method and endpoint.
        """
        def test_method(self):
            response = self.perform_test(method, endpoint, data, headers)
            self.assertEqual(
                response.status_code, 
                200 if method != 'DELETE' else 404,
            )
        return test_method
    
    def add_route_tests(self, route, filenames, allowed_methods, data=None):
        """
        Helper function to add test methods for a specific route.
        """
        for method in allowed_methods:
            for filename in filenames:
                endpoint = f"/{route}/{filename}"
                headers = {"Authorization": "api_key"}
                test_method = self.create_test_method(method, endpoint, data, headers)
                test_name = f"test_{method.lower()}_{route.replace('/', '_')}_{filename.replace('.', '_')}"
                setattr(self, test_name, test_method)
                
    def test_images_routes(self):
        """
        Test methods for '/media/images/' routes.
        """
        image_filenames = ['example1.jpg', 'example2.jpg']    # change the examples
        allowed_methods = ['GET', 'POST']
        # self.add_route_tests('media/images', image_filenames, allowed_methods)
        for method in allowed_methods:
            for filename in image_filenames:
                endpoint = f"/media/images/{filename}" 
                headers = {"Authorization": "api_key"}

                if method == 'POST':
                    with open(os.path.join('tests', filename), 'rb') as f:
                        data = {'file': (f, filename)}
                    test_method = self.create_test_method(method, endpoint, data, headers)
                else:
                    test_method = self.create_test_method(method, endpoint, headers=headers)
                        
    def test_files_routes(self):
        """
        Test methods for 'media/files/' routes.
        """
        text_filenames = ['example1.docx', 'example2.docx'] # change the examples
        allowed_methods = ['GET', 'POST']
        self.add_route_tests('media/files', text_filenames, allowed_methods)
        
    def test_unauthorized_upload(self):
        """
        Test upload without authorization header.
        """
        data = {"file": (b"test_content", "test.txt")}
        response = self.perform_test("POST", "/media/files", data)
        self.assertEqual(response.status_code, 401)
        
if __name__ == "__main__":
    unittest.main()