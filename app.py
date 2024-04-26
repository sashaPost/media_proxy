from flask import Blueprint, Flask, Response, request, send_from_directory, jsonify
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
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from dotenv import load_dotenv


load_dotenv() 

app = Flask(__name__)
setup_blueprint = Blueprint('setup', __name__)
app.config['SECRET_KEY'] = str(secrets.SystemRandom().getrandbits(128))
app.config['MAX_CONTENT_LENGTH'] = 24 * 1024 * 1024    # Limit file size to 24MB

API_KEY = os.getenv('API_KEY')
ALLOWED_EXTENSIONS = {'image': set(['jpeg', 'jpg', 'png', 'gif']),
                                    'document': set(['docx', 'pdf'])}   # !!! add '.doc' !!!
ALLOWED_DIRECTORIES = ['images', 'files']
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


@setup_blueprint.before_app_request
def directories_check():
    """
    Creates media directories on first request.
    """
    logger.info("*** 'directories_check' was triggered ***")
    # dest_dir = None
    try:
        os.makedirs(app.config['MEDIA_FILES_DEST'], exist_ok=True)
        for directory in ALLOWED_DIRECTORIES:
            dest_dir = os.path.join(app.config['MEDIA_FILES_DEST'], directory)
            os.makedirs(dest_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create directory {dest_dir}: {e}")


app.register_blueprint(setup_blueprint)


def check_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(request.headers.get("Authorization"))
        if request.headers.get("Authorization") != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)
    return wrapper


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
            
            
def is_valid_image(uploaded_file):
    """Checks if an uploaded file is a valid image.

    Args:
        uploaded_file (FileStorage): The Flask uploaded file object.

    Returns:
        bool: True if the file is a valid image, False otherwise.
    """
    logger.info("*** 'is_valid_image' was triggered ***") 
    
    stream = uploaded_file.stream
    mime = magic.Magic()
    file_type_description = mime.from_buffer(stream.read(4096))
    stream.seek(0)
    logger.info(f"'file_type_description': {file_type_description}")
    
    logger.info(f"'uploaded_file.content_type': {uploaded_file.content_type}")
    
    try:
        img = Image.open(uploaded_file.stream)
        logger.info(f"'Image.open(uploaded_file.stream)': {img}")
        # logger.info(dir(img))
        # file_type = img.format.lower()
        # logger.info(f"'file_type': {file_type}")
        # if file_type not in ALLOWED_EXTENSIONS['image']:
        #     return False
        return True
    except (IOError, OSError) as e:
        logger.warning(f"Failed to open image using Pillow: {e}")
        return False   
    
    
def is_valid_docx(uploaded_file):
    """Checks if an uploaded file is a valid .docx document.

    Args:
        uploaded_file (FileStorage): The Flask uploaded file object.

    Returns:
        bool: True if the file is a valid .docx document, False otherwise.
    """
    logger.info(f"'is_valid_docx' was triggered")
    logger.info("Validating DOCX file...")

    try: 
        document = docx.Document(io.BytesIO(uploaded_file.read()))
        logger.info(f"'document': {document}")
        logger.info("DOCX file validated successfully.")
        return True
    except docx.opc.exceptions.PackageNotFoundError as e:
        logger.warning(f"Not a valid DOCX file: {e}")
        return False
    except Exception as e:
        logger.error(f"Error processing DOCX file: {e}")
        return False
        
    
def is_valid_pdf(uploaded_file):
    """Checks if an uploaded file is a valid .pdf document.

    Args:
        uploaded_file (FileStorage): The Flask uploaded file object.

    Returns:
        bool: True if the file is a valid .pdf document, False otherwise.
    """
    logger.info("* 'is_valid_pdf' was triggered *")
    logger.info("Validating PDF file...")
    
    try:
        # pdf_obj = PdfReader(uploaded_file)
        # logger.info(f"'pdf_obj': {pdf_obj}\n'type': {type(pdf_obj)}")
        # if pdf_obj:
        #     return True
        PdfReader(uploaded_file)  # Simpler validation check is sufficient
        logger.info("PDF file validated successfully.")
        return True
    except PdfReadError as e:
        logger.warning(f"Not a valid PDF file: {e}")
        return False
    except Exception as e:
        logger.error(f"Error processing PDF file: {e}")
        return False
    
    
def is_valid_file(uploaded_file):
    """Determines if an uploaded file is a valid .docx or .pdf document.

    Args:
        uploaded_file (FileStorage): The Flask uploaded file object.

    Returns:
        bool: True if the file is valid, False otherwise.
    """
    logger.info("* 'is_valid_file' was triggered *") 
    
    logger.info(f"'uploaded_file': {uploaded_file}") 
    
    file_extension = uploaded_file.filename.split('.')[-1].lower()  
    logger.info(f"'file_extension': {file_extension}")
    
    mime = magic.Magic()
    file_type_description = mime.from_buffer(uploaded_file.stream.read(4096))
    uploaded_file.stream.seek(0)
    logger.info(f"'file_type_description': {file_type_description}")
        
    if file_extension == 'docx':
        logger.info("Uploaded file was recognized as '.docx'.")
        # if is_valid_docx(uploaded_file):
        #     return True
        return is_valid_docx(uploaded_file)
    elif file_extension == 'pdf':
        logger.info("Uploaded file was recognized as '.pdf'.")
        # if is_valid_pdf(uploaded_file):
        #     return True
        return is_valid_pdf(uploaded_file)
    else:
        logger.warning(f"Unsupported file type: {file_type_description}")
        return False
        
        
def path_secure(origin_file_path, file_key):
    """Secures the destination path for an uploaded file.

    Determines the appropriate subdirectory ('images' or 'files') based on 
    file type and constructs a safe, sanitized filename.

    Args:
        origin_file_path (str): The original file path provided by the user.
        file_key (str): Key in the 'request.files' dictionary ('image' or 'file').

    Returns:
        str: The secured file path ready for saving the uploaded file.
        None: If a directory traversal is attempted.
        False: If an invalid file type is detected.
    """
    logger.info("*** 'path_secure' triggered ***")
    
    logger.info(f"'file_key': {file_key}")
    
    uploaded_file = request.files[file_key]
    logger.info(f"'uploaded_file': {uploaded_file}")

    secured_filename = secure_filename(uploaded_file.filename)
    logger.info(f"'file_name': {secured_filename}")
    
    dest_dir = origin_file_path.split('/')[-2]
    logger.info(f"'dest_dir': {dest_dir}")
    if dest_dir not in ['images', 'files']:
        return Response("Directory not allowed", status=403)
    
    if is_valid_image(uploaded_file):
        allowed_path = os.path.join(app.config['MEDIA_FILES_DEST'], 'images')
        logger.info(f"'allowed_path': {allowed_path}")
    elif is_valid_file(uploaded_file):  
        
        allowed_path = os.path.join(app.config['MEDIA_FILES_DEST'], 'files')
        logger.info(f"'allowed_path': {allowed_path}")
    else:  
        logger.warning("Invalid file type")
        return False 
        
    logger.info(f"'secured_filename': {secured_filename}")
    logger.info(f"'allowed_path': {allowed_path}")
    result_path = os.path.join(allowed_path, secured_filename)
    logger.info(f"'result_path': {result_path}")
    return result_path

def get_file_extension(origin_file_path):
    """Determines whether the file extension in the provided path is allowed.

    Checks if the extracted file extension exists in the list of allowed 
    extensions for images or documents.

    Args:
        origin_file_path (str): The file path to be analyzed.

    Returns:
        bool: True if the file extension is supported, False otherwise.
    """
    logger.info("*** 'get_file_extension' was triggered ***")
    file_extension = origin_file_path.split('.')[-1]
    logger.info(f"'file_extension': {file_extension}")
    
    if file_extension not in ALLOWED_EXTENSIONS['image'] \
        and file_extension not in ALLOWED_EXTENSIONS['document']:
        return False
    return True
     
def get_request_directory(req_abs_file_path):
    """Splits the absolute file path by the '/' separator and rejoins all 
    elements except the last one (the filename), providing the directory.

    Args:
        req_abs_file_path (str): The absolute file path to process.

    Returns:
        str: The extracted directory absolute path.
    """
    logger.info("*** 'get_request_directory' was triggered ***")
    logger.info(f"'req_abs_file_path': {req_abs_file_path}")
    
    parts = req_abs_file_path.split('/')
    logger.info(f"directory: {'/'.join(parts[:-1])}")
    return '/'.join(parts[:-1])
    
def is_valid_file_path(origin_file_path):
    """Validates a file path for security and allowed locations.

    Checks if the constructed absolute file path:
        * Resides within the configured media directory.
        * Points to an existing directory.
        * Belongs to a specifically allowed subdirectory.

    Args:
        origin_file_path (str): The relative file path provided in the request.

    Returns:
        bool: True if the file path is valid, False otherwise.
    """
    logger.info(f"*** 'is_valid_file_path' was triggered ***")
    
    logger.info(f"'origin_file_path': {origin_file_path}")
    
    req_abs_file_path = os.path.abspath(os.path.normpath(os.path.join(app.config['MEDIA_FILES_DEST'], origin_file_path)))
    logger.info(f"'req_abs_file_path': {req_abs_file_path}")
    
    media_abs_path = os.path.abspath(app.config['MEDIA_FILES_DEST'])
    logger.info(f"'media_abs_path': {media_abs_path}")
    
    allowed_dirs = [ os.path.join(media_abs_path, directory) for directory in ALLOWED_DIRECTORIES ]
    logger.info(f"'allowed_dirs': {allowed_dirs}")
    
    req_dir = get_request_directory(req_abs_file_path)
    logger.info(f"'req_dir': {req_dir}")
    
    if os.path.exists(req_dir) and req_abs_file_path.startswith(media_abs_path):
        if req_dir in allowed_dirs:
            return True
    logger.warning(f"'req_abs_file_path': {req_abs_file_path}")
    return False

def allowed_path_and_extension(origin_file_path):
    """Checks if a file path is valid and has an allowed extension.

    Performs the following validations:
        *  The file path must be valid according to security and location constraints.
           (`is_valid_file_path` check).
        *  The file must have a supported file extension (`get_file_extension` check).

    Args:
        origin_file_path (str): The relative file path provided in the request.

    Returns:
        bool: True if the path is valid and the extension is allowed, False otherwise.
    """
    logger.info("*** 'allowed_path_and_extension' was triggered ***")
    logger.info(f"'origin_file_path': {origin_file_path}")
    
    if is_valid_file_path(origin_file_path) and get_file_extension(origin_file_path):
        logger.info("'allowed_path_and_extension' retruns True")
        return True
    return False

def handle_upload(origin_file_path):
    """Coordinates the file upload process, performing validations and saving.

    Handles the following steps:
        * Checks if a valid file ('image' or 'file') is present in the request.
        * Validates the file size against the configured maximum limit.
        * Checks for an empty filename.
        * Ensures the file path is allowed and has a supported extension.
        * Secures the destination path.
        * Saves the uploaded file to disk and sets appropriate permissions.

    Args:
        origin_file_path (str): The relative file path provided in the request.

    Returns:
        True:  If the upload process is successful.
        False: If any validation fails or an error occurs during the upload.
        Response:  If no suitable file is found in the request or the file size is too large.
    """
    logger.info("*** 'handle_upload' was triggered ***")
    logger.info(f"'origin_file_path': {origin_file_path}")
    logger.info(f"'request.files': {request.files}")

    if 'image' not in request.files and 'file' not in request.files:
        # logger.warning("'file' not in 'request.files'")
        logger.warning(f"'request.files': {request.files}")
        return Response("No file part", status=400)
    
    file_key = 'image' if 'image' in request.files else 'file' 
    try:
        uploaded_file = request.files[file_key]
        logger.info(f"'uploaded_file': {uploaded_file}")
        
        # There's no need in file size check implementation - Werkzeug is responsible for that by default 
        
        if uploaded_file.filename == '':
            logger.warning("uploaded_file.filename == ''")
            return Response("Empty filename", status=400)
            
        try:
            if allowed_path_and_extension(origin_file_path):
                logger.info("passed 'if allowed_path_and_extension(origin_file_path)'")
                secured_path = path_secure(origin_file_path, file_key)
                logger.info(f"'secured_path': {secured_path}")
                
                with open(secured_path, 'wb') as destination_file: 
                    uploaded_file.save(destination_file)
                os.chmod(secured_path, 0o755)  
                logger.info("SUCCESS")
                return True
            else:
                logger.warning("!!! 'if allowed_path_and_extension' failed !!!")
                return False
        except Exception as e:
            logger.info(f"Exception: {e}")
            logger.warning(f"!!! 'handle_upload' failed !!!")
            return False
    except Exception as e:
        logger.info(f"Exception: {e}")
        return False
        
@app.route('/media/<path:origin_file_path>', methods=['POST'])
@check_api_key
def upload_file(origin_file_path):    
    """Handles file upload requests.

    Performs the following:
        * Logs the request.
        * Delegates the upload process to the `handle_upload` function.
        * Returns an appropriate response (success or error) based on the result of `handle_upload`.

    Args:
        origin_file_path (str): The relative file path extracted from the URL.
    """
    logger.info("*** 'upload_file' was triggered ***")
    logger.info("'POST' method detected")
    logger.info(f"'origin_file_path': {origin_file_path}")
        
    if handle_upload(origin_file_path):
        return Response("OK", status=200)
    return Response("Error uploading file", status=501)

if __name__ == '__main__':
    app.run()
    