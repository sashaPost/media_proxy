from flask import Flask, Response, request, send_from_directory, jsonify
# import imghdr   # Determine the type of an image
from werkzeug.utils import secure_filename
import os
import secrets
import logging
from urllib.parse import quote_plus, urlparse
from functools import wraps
from PIL import Image
import magic
import docx
import io


app = Flask(__name__)
app.config['SECRET_KEY'] = str(secrets.SystemRandom().getrandbits(128))
app.config['MAX_CONTENT_LENGTH'] = 24 * 1024 * 1024    # Limit file size to 24MB
ALLOWED_EXTENSIONS = {'image': set(['jpeg', 'jpg', 'png', 'gif']),
                                    'document': set(['docx', 'pdf'])}
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

def check_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(request.headers.get("Authorization"))
        if request.headers.get("Authorization") != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)
    return wrapper

def is_valid_file_path(file_path):
    requested_file_path = os.path.abspath(os.path.normpath(os.path.join(app.config['MEDIA_FILES_DEST'], file_path)))
    logger.info(f"os.path.abspath(app.config['MEDIA_FILES_DEST']): {os.path.abspath(app.config['MEDIA_FILES_DEST'])}")
    return os.path.exists(requested_file_path) and requested_file_path.startswith(os.path.abspath(app.config['MEDIA_FILES_DEST']))

def get_file_extension(origin_file_path):
    file_extension = origin_file_path.split('.')[-1]
    
    if file_extension not in ALLOWED_EXTENSIONS['image'] \
        and file_extension not in ALLOWED_EXTENSIONS['document']:
        return False, file_extension
    return True,
     
    # return file_extension


def allowed_extension(origin_file_path):
    """    
    Should be called in 'upload_file' before 'path_secure()'.
    Performs check by file extension only (from origin file path).
    If 'origin_path' != 'allowed_path' return False without checking file extension.
    # return Bool
    """
    logger.info("*** 'allowed_extension' was triggered ***")
    logger.info(f"'origin_file_path': {origin_file_path}")
    
    if get_file_extension(origin_file_path):
        return True
    return False
    
    # allowed_image_path = os.path.join(app.config['MEDIA_FILES_DEST'], 'images')
    # allowed_extension_path = os.path.join(app.config['MEDIA_FILES_DEST'], 'files')
    # valid_paths = ['media/images', 'media/files']
    # If 'origin_path' != 'allowed_path' return False without checking file extension.
    # time to perform check
    # reminder: 
    # os.makedirs(allowed_path, exist_ok=True)
    # if check passed deattach file name from path.
    
    # file_name = origin_file_path.split('/')[-1]
    # logger.info(f"'file_name': {file_name}")
    
    # file_extension = file_name.split('.')[-1].lower()
    # logger.info(f"'file_extension': {file_extension}")
    # file_extension = extract_file_extension(origin_file_path)
    # if file_extension ...
    
    # uploaded_file = request.files['file']
    # logger.info(f"'uploaded_file': {uploaded_file}")
    # logger.info(f"'uploaded_file.content_type': {uploaded_file.content_type}")
    
    # if uploaded_file.content_type.startswith('application/'):
    #     return uploaded_file.content_type, True
    
    # # if uploaded_file.content_type.startswith('image/'):
    # try:
    #     Image.open(uploaded_file.stream)
    #     # return uploaded_file.content_type, True
    #     return True
    # except (IOError, OSError) as e:
    #     logger.warning(f"Failed to open image using Pillow: {e}")
    #     return False   
        
    
    # return False
            
def is_valid_image(uploaded_file):
    logger.info("*** 'is_valid_image' was triggered ***") 
    
    stream = uploaded_file.stream
    mime = magic.Magic()
    # file_type_description = mime.from_buffer(file_stream.read(1024))
    file_type_description = mime.from_buffer(stream.read(4096))
    stream.seek(0)
    logger.info(f"'file_type_description': {file_type_description}")
    
    logger.info(f"'uploaded_file.content_type': {uploaded_file.content_type}")
    
    if uploaded_file.content_type.startswith('image/'):
        try:
            Image.open(uploaded_file.stream)
            logger.info(f"'Image.open(uploaded_file.stream)': {Image.open(uploaded_file.stream)}")
            return True
        except (IOError, OSError) as e:
            logger.warning(f"Failed to open image using Pillow: {e}")
            return False   
    
    # if 'image' in file_type_description:
    #     return True
    # return False

def is_valid_file(file_stream):
    logger.info("* 'is_valid_file' was triggered *") 
    logger.info(f"'file_stream': {file_stream}") 
    
    file_bytes = file_stream.read()
    try: 
        document = docx.Document(io.BytesIO(file_bytes))
        logger.info(f"'document': {document}")
        return True
    except docx.opc.exceptions.PackageNotFoundError as e:
        logger.warning(f"{e}")
        return False
        
def path_secure(origin_file_path):
    """
    !!! provide it with 'origin_file_path'
    Should return secured file path or False.
    """
    logger.info("*** 'path_secure' triggered ***")
    
    uploaded_file = request.files['file']
    logger.info(f"'uploaded_file': {uploaded_file}")
    
    # * was already checked in 'handle_upload'!
    # if not uploaded_file:
    #     logger.warning("No file was provided")
    #     return Response

    secured_filename = secure_filename(uploaded_file.filename)
    logger.info(f"'file_name': {secured_filename}")
    
    dest_dir = origin_file_path.split('/')[-2]
    logger.info(f"'dest_dir': {dest_dir}")
    if dest_dir not in ['images', 'files']:
        return Response("Directory not allowed", status=403)
    
    # allowed_path = os.path.join(app.config['MEDIA_FILES_DEST'], 'images')
    # os.makedirs(allowed_path, exist_ok=True)
    # logger.info(f"'allowed_path': {allowed_path}")
    # result_path = os.path.join(allowed_path, filename)
    # logger.info(f"'result_path': {result_path}")
    # return result_path
    
    # !!! SHOULDN'T CALL 'is_valid_image/is_valid_file' !!! 
    # Prioritize image check
    if is_valid_image(uploaded_file):
        allowed_path = os.path.join(app.config['MEDIA_FILES_DEST'], 'images')
        logger.info(f"'allowed_path': {allowed_path}")
    elif is_valid_file(uploaded_file.stream):  # Now check for Word documents
        allowed_path = os.path.join(app.config['MEDIA_FILES_DEST'], 'files')
        logger.info(f"'allowed_path': {allowed_path}")
    else:  # Fallback if neither image nor document
        logger.warning("Invalid file type")
        return False 
    
    os.makedirs(allowed_path, exist_ok=True)
    
    logger.info(f"'secured_filename': {secured_filename}")
    logger.info(f"'allowed_path': {allowed_path}")
    result_path = os.path.join(allowed_path, secured_filename)
    logger.info(f"'result_path': {result_path}")
    return result_path

def handle_upload(origin_file_path):
    """
    - function should perform a superficial check if file type is allowed at first (by extension - 'allowed_extension');
    - after that should secure it's destination path ('path_secure')
    """

    logger.info("*** 'handle_upload' was triggered ***")
    logger.info(f"'origin_file_path': {origin_file_path}")
    # logger.info(request.files['file'])
    if 'file' not in request.files:
        logger.warning("'file' not in 'request.files'")
        logger.warning(f"{request.files}")
        return Response("No file part", status=400)
    
    uploaded_file = request.files['file']
    logger.info(f"'uploaded_file': {uploaded_file}")
    
    if uploaded_file.stream.tell() > app.config['MAX_CONTENT_LENGTH']:
        logger.warning("File size exceeds allowed limit")
        return Response("File size exceeds allowed limit", status=413)
    
    if uploaded_file.filename == '':
        logger.warning("uploaded_file.filename == ''")
        return Response("Empty filename", status=400)
    
    # 
    if allowed_extension(origin_file_path):
        try:
            secured_path = path_secure(origin_file_path)
            logger.info(f"'secured_path': {secured_path}")
            uploaded_file.save(secured_path)
            logger.info("SUCCESS")
            return Response("File was uploaded successfully", status=200)
        except Exception as e:
            logger.info(f"Exception: {e}")
            logger.warning(f"!!! 'handle_upload' failed !!!")
            return Response("Error handling file", status=501)
    
@app.route('/media/<path:origin_file_path>', methods=['POST'])
@check_api_key
def upload_file(origin_file_path):    
    logger.info("*** 'upload_file' was triggered ***")
    logger.info("'POST' method detected")
    logger.info(f"'origin_file_path': {origin_file_path}")
    
    try:
        handle_upload(origin_file_path)
        return Response("OK", status=200)
    except Exception as e:
        logger.warning(f"Exception: {e}")
        return Response("Error uploading file", status=501)
            
if __name__ == '__main__':
    app.run()
    