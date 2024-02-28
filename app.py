from flask import Flask, Response, request, send_from_directory, jsonify
# import imghdr   # Determine the type of an image
from werkzeug.utils import secure_filename
import os
import secrets
import logging
from urllib.parse import quote_plus, urlparse
from functools import wraps
from PIL import Image



app = Flask(__name__)
app.config['SECRET_KEY'] = str(secrets.SystemRandom().getrandbits(128))
app.config['MAX_CONTENT_LENGTH'] = 24 * 1024 * 1024    # Limit file size to 24MB
app.config['ALLOWED_EXTENSIONS'] = ['jpeg', 'jpg', 'png', 'gif', 'doc', 'docx']
# app.config['UPLOADED_IMAGES_DEST'] = 'media/images'
# app.config['UPLOADED_FILES_DEST'] = 'media/files'
app.config['MEDIA_FILES_DEST'] = 'media'
app.config['ENV'] = 'production'
app.config['DEBUG'] = False

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

API_KEY = "api_key"



def check_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(request.headers.get("Authorization"))
        if request.headers.get("Authorization") != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)
    return wrapper

def is_valid_file_path(file_path):
    requested_file_path = os.path.abspath(os.path.join(app.config['MEDIA_FILES_DEST'], file_path))
    logger.info(f"requested_file_path: {requested_file_path}")
    return os.path.exists(requested_file_path) \
        and requested_file_path.startswith(os.path.abspath(app.config['MEDIA_FILES_DEST']))

def allowed_file(file_name):
    logger.info("'allowed_file' was triggered.")
    logger.info(f"'file_name': {file_name}")
    logger.info(f"File extension: {file_name.split('.')[-1].lower()}")
    
    if file_name.split('.')[-1].lower() not in app.config['ALLOWED_EXTENSIONS']:
        return False
    
    uploaded_file = request.files['file']
    
    if uploaded_file.content_type.startswith('image/'):
        try:
            Image.open(uploaded_file.stream)
            return uploaded_file.content_type, True
        except (IOError, OSError) as e:
            logger.warning(f"Failed to open image using Pillow: {e}")
            return False   
        
    if uploaded_file.content_type.startswith('application/'):
        return uploaded_file.content_type, True
    
    return False
            

def secure_name(file_path):
    uploaded_file = request.files['file']
    content_type = uploaded_file.content_type
    logger.info(f"'secure_name' 'content_type': {content_type}")
    
    logger.info(file_path) 
    safe_filename = secure_filename(os.path.basename(file_path))  # Sanitize filename only
    logger.info(safe_filename) 
    
    if content_type.startswith('image/'):
        allowed_path = os.path.join(app.config['MEDIA_FILES_DEST'], "images")
        result_path = os.path.join(allowed_path, safe_filename)
        logger.info(f"'result_path': {result_path}")
        return result_path
    elif content_type.startswith('application/'):
        allowed_path = os.path.join(app.config['MEDIA_FILES_DEST'], "files")
        result_path = os.path.join(allowed_path, safe_filename)
        logger.info(f"'result_path': {result_path}")
        return result_path
    else:
        return False

def handle_upload(file_path):
    logger.info("'POST' method detected")
    logger.info(f"'handle_upload' origin 'file_path': {file_path}")
    # logger.info(request.files['file'])
    if 'file' not in request.files:
        logger.warning("'file' not in 'request.files'")
        logger.warning(f"{request.files}")
        return Response("No file part", status=400)
    
    uploaded_file = request.files['file']
    logger.info(f"'uploaded_file': {uploaded_file}")
    
    if uploaded_file.filename == '':
        logger.warning("uploaded_file.filename == ''")
        return Response("No selected file", status=400)
    
    logger.info(f"allowed_file: {allowed_file(uploaded_file.filename)}")
    content_type, is_allowed_file = allowed_file(uploaded_file.filename)
    logger.info(f"content_type: {content_type}")
    # logger.info(f"path: {path}")
    logger.info(f"is_allowed_file: {is_allowed_file}")
    if not is_allowed_file:
        logger.warning("FILE TYPE IS NOT ALLOWED")
        return Response("File type not allowed", status=400)
    else:
        logger.info(f"'uploaded_file.filename': {uploaded_file.filename}")
        try:
            uploaded_file.save(file_path)
            logger.info("SUCCESS")
            return Response("File was uploaded successfully", status=200)
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return Response("Error uploading file", status=500)

# implements the GET method logic:
@app.route('/media/<path:file_path>', methods=['GET'])
def handle_get_request(file_path):
    logger.info(f"'file_path': {file_path}")
    logger.info("'GET' method detected")
    try:
        logger.info(f"'os.path.dirname': {os.path.dirname(file_path)}")
        logger.info(f"'os.path.basename': {os.path.basename(file_path)}")
        return send_from_directory(os.path.join(app.config['MEDIA_FILES_DEST'], \
            os.path.dirname(file_path)), os.path.basename(file_path))
    except FileNotFoundError:
        return Response("File not found", status=404)
    except Exception as e:
        return Response("Unsupported method", status=405)
        # return Response("Error: {}".format(str(e)), status=500)
    

@app.route('/media/<path:file_path>', methods=['POST'])
@check_api_key
def upload_file(file_path):
    logger.info("'upload_file' was triggered.")
    logger.info(f"'file_path': {file_path}")
    
    result_path = secure_name(file_path)
    logger.info(f"'result_path': {result_path}")
    
    if result_path:
        return handle_upload(result_path)
    else:
        return Response("Error uploading file", status=501)
        
    
if __name__ == '__main__':
    app.run()
    
    

# it worked:
# def allowed_file(file_name):
#     return '.' in file_name and \
#         file_name.rsplit('.', 1)[1].lower() in app.config['UPLOAD_EXTENSIONS']
        
# def urlparse_reconstruct(scheme, netloc, path, params={}, query='', fragment=''):
#     return urlparse(f"{scheme}://{netloc}{path}?{query}#{fragment}", allow_fragments=True)

# def sanitize_url(url):
#     parsed_url = urlparse(url)
#     logger.info(f"parsed_url.scheme: {parsed_url.scheme}")
#     logger.info(f"parsed_url.netloc: {parsed_url.netloc}")
#     logger.info(f"parsed_url.path: {parsed_url.path}")
#     logger.info(f"query: {quote_plus(parsed_url.query)}")
#     logger.info(f"parsed_url.fragment: {parsed_url.fragment}")
#     cleaned_parts = {
#         "scheme": parsed_url.scheme,
#         "netloc": parsed_url.netloc,
#         "path": parsed_url.path,
#         "params": {},
#         "query": quote_plus(parsed_url.query),
#         "fragment": parsed_url.fragment,
#     }
#     return urlparse_reconstruct(**cleaned_parts)

# def sanitize_url(url):
#     parsed_url = urlparse(url)
#     cleaned_path = quote_plus(parsed_url.path)
    # return cleaned_path
    
    
    # if filename.split('/')[0] == 'images':
    #     logger.info("IMAGE REQUEST")
    #     file_path = os.path.join(app.config['UPLOADED_IMAGES_DEST'], filename)
    #     logger.info(f"'file_path': {file_path}")
    #     logger.info(f"'filename': {filename}")
    #     return handle_request(file_path, request.method)
    # else:
    #     logger.info("FILE REQUEST")
    #     file_path = os.path.join(app.config['UPLOADED_FILES_DEST'], filename)
    #     logger.info(f"'file_path': {file_path}")
    #     logger.info(f"'filename': {filename}")
    #     return handle_request(file_path, request.method)
        
    
# @app.route('/media/files/<filename>', methods=['GET', 'POST', 'PUT', 'DELETE'])
# def handle_files(filename):
#     file_path = os.path.join(app.config['UPLOADED_FILES_DEST'], filename)
#     return handle_request(file_path, request.method)
    
    
    
    
# @app.route('/media/images/<filename>', methods=['GET', 'POST', 'PUT', 'DELETE'])
# def handle_images(filename):
#     if request.method == 'GET':
#         file_path = os.path.join(app.config['UPLOADED_IMAGES_DEST'], filename)
#         try:
#             with open(file_path, 'rb') as file:
#                 content = file.read()
#             return Response(content, mimetype='application/octet-stream')
#         except FileNotFoundError:
#             return Response("File not found", status=404)
#         except Exception as e:
#             return Response("Error: {}".format(str(e)), status=500)

#     elif request.method == 'POST':
#         if 'file' not in request.files:
#             return Response("No file part", status=400)
#         uploaded_file = request.files['file']
#         if uploaded_file.filename == '':
#             return Response("No selected file", status=400)
#         if not allowed_file(uploaded_file.filename):
#             return Response("File type not allowed", status=400)
#         else:
#             filename = secure_filename(uploaded_file.filename)
#             file_path = os.path.join(app.config['UPLOADED_IMAGES_DEST'], filename)
#             uploaded_file.save(file_path)
#             return Response("File was uploaded successfully", status=200)

#     elif request.method == 'PUT':
#         file_path = os.path.join(app.config['UPLOADED_IMAGES_DEST'], filename)
#         if not os.path.exists(file_path):
#             return Response("File does not exist", status=404)
#         if 'file' not in request.files:
#             return Response("No file part", status=400)
#         uploaded_file = request.files['file']
#         if uploaded_file.filename == '':
#             return Response("No selected file", status=400)
#         if not allowed_file(uploaded_file.filename):
#             return Response("File type not allowed", status=400)
#         else:
#             uploaded_filename = secure_filename(uploaded_file.filename)
#             uploaded_file_path = os.path.join(app.config['UPLOADED_IMAGES_DEST'], uploaded_filename)
#             # Remove the old file and replace it with the new one
#             os.remove(file_path)
#             uploaded_file.save(uploaded_file_path)
#             os.rename(uploaded_file_path, file_path)
#             return Response("File was updated successfully", status=200)

#     elif request.method == 'DELETE':
#         file_path = os.path.join(app.config['UPLOADED_IMAGES_DEST'], filename)
#         if os.path.exists(file_path):
#             os.remove(file_path)  # Remove the file
#             return Response("File was deleted successfully", status=200)
#         else:
#             return Response("File not found", status=404)
#     return Response("Unsupported method", status=405)


# was a part of 'allowed_file' function:
    # content_type = uploaded_file.content_type
    
    # if content_type.startswith('image/') and imghdr.what(uploaded_file.stream) != content_type.split('/')[1]:
        # logger.info(f"content_type.startswith('image/'): {content_type.startswith('image/')}")
        # logger.info(f"imghdr.what(uploaded_file.stream): {imghdr.what(uploaded_file.stream)}")
        # logger.info(f"content_type.split('/')[1]: {content_type.split('/')[1]}")
        # logger.info(f"It seems to me this shit fucks everything up.")
        # return False
    # if content_type.startswith('image/'):
    #     limited_bytes = uploaded_file.stream.read(1024)
    #     # uploaded_file.stream.seek(0)  
        
    #     image_format = imghdr.what(limited_bytes)
    #     if image_format:
    #         if image_format.lower() != content_type.split('/')[1]:
    #             logger.info(f"Content type mismatch: {content_type} vs {image_format}")
    #             # Consider handling the content type mismatch
    #             return False
    #         else:
    #             return True
    #     else:
    #         logger.warning("Failed to identify image format using imghdr.")
    #         # Consider implementing alternative checks or rejecting the upload
    #         return False
    # return True