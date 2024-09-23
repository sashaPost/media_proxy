import re
from flask import Blueprint, Flask, Response, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import os
import secrets
import logging
from functools import wraps
from PIL import Image
import magic
import docx
from PyPDF2 import PdfReader
import olefile
from dotenv import load_dotenv
import tempfile
import io
import struct
import zipfile

load_dotenv()

app = Flask(__name__)
setup_blueprint = Blueprint("setup", __name__)
app.config["SECRET_KEY"] = str(secrets.SystemRandom().getrandbits(128))
app.config["MAX_CONTENT_LENGTH"] = 24 * 1024 * 1024  # Limit file size to 24MB

API_KEY = os.getenv("API_KEY")
ALLOWED_EXTENSIONS = {
    "image": set(["jpeg", "jpg", "png", "gif"]),
    "document": set(["docx", "pdf", "doc"]),
}
ALLOWED_DIRECTORIES = ["images", "files"]
app.config["MEDIA_FILES_DEST"] = "media"
app.config["ENV"] = "production"
# app.config['ENV'] = 'development'
app.config["DEBUG"] = False
# app.config['DEBUG'] = True

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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
        os.makedirs(app.config["MEDIA_FILES_DEST"], exist_ok=True)
        for directory in ALLOWED_DIRECTORIES:
            dest_dir = os.path.join(app.config["MEDIA_FILES_DEST"], directory)
            os.makedirs(dest_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create directory {dest_dir}: {e}")


app.register_blueprint(setup_blueprint)


def check_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Request API key: {request.headers.get('Authorization')}")
        logger.info(f"Source API key: {API_KEY}")
        if request.headers.get("Authorization") != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)

    return wrapper


# implements the GET method logic:
@app.route("/media/<path:file_path>", methods=["GET"])
def handle_get_request(file_path):
    logger.info(f"'file_path': {file_path}")
    logger.info("'GET' method detected")
    try:
        logger.info(f"'os.path.dirname': {os.path.dirname(file_path)}")
        logger.info(f"'os.path.basename': {os.path.basename(file_path)}")
        return send_from_directory(
            os.path.join(app.config["MEDIA_FILES_DEST"], os.path.dirname(file_path)),
            os.path.basename(file_path),
        )
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

    try:
        # Read the file content
        file_content = uploaded_file.read()
        uploaded_file.seek(0)

        # Check the file type using python-magic
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(file_content)
        logger.info(f"Detected MIME type: {mime_type}")

        if not mime_type.startswith("image/"):
            logger.warning(f"File is not an image: {mime_type}")
            return False

        # Open and verify the image using Pillow:
        with Image.open(io.BytesIO(file_content)) as img:
            img.verify()
            logger.info(
                f"Image format: {img.format}, Size: {img.size}, Mode: " f"{img.mode}"
            )

            # Check for unusually large images
            if img.size[0] > 8000 or img.size[1] > 8000:
                logger.warning(f"Image dimensions are suspiciously large: {img.size}")
                return False

            # Check for format-specific vulnerabilities
            if img.format == "JPEG":
                # Check for JPEG comment injection
                if b"comment" in file_content.lower():
                    logger.warning("Potential JPEG comment injection detected")
                    return False
            elif img.format == "PNG":
                # Check for PNG chunks that might contain malicious data
                offset = 8
                while offset < len(file_content):
                    chunk_length, chunk_type = struct.unpack(
                        ">I4s", file_content[offset : offset + 8]
                    )
                    if chunk_type in [b"IEND", b"IHDR"]:
                        break
                    if chunk_type not in [
                        b"IHDR",
                        b"IDAT",
                        b"IEND",
                        b"PLTE",
                        b"tRNS",
                        b"cHRM",
                        b"gAMA",
                        b"iCCP",
                        b"sBIT",
                        b"sRGB",
                        b"tEXt",
                        b"zTXt",
                        b"iTXt",
                        b"bKGD",
                        b"hIST",
                        b"pHYs",
                        b"sPLT",
                        b"tIME",
                    ]:
                        logger.warning(f"Suspicious PNG chunk detected: {chunk_type}")
                        return False
                    offset += chunk_length + 12
            elif img.format == "GIF":
                # Check for potential GIF Polyglots
                if b"<script" in file_content or b"<svg" in file_content:
                    logger.warning("Potential GIF polyglot detected")
                    return False

            logger.info("Image validated successfully")
            return True
    except Exception as e:
        logger.warning(f"Failed to validate image: {e}")
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
        uploaded_file.stream.seek(0)
        pdf_content = uploaded_file.stream.read()
        pdf_file = io.BytesIO(pdf_content)
        reader = PdfReader(pdf_file)

        # Check for JavaScript
        for page in reader.pages:
            if "/JS" in page or "/JavaScript" in page:
                logger.warning(
                    "PDF contains JavaScript, which could be potentially " "harmful."
                )
                return False

        # Check for embedded files
        if "/EmbeddedFiles" in reader.trailer["/Root"]:
            logger.warning(
                "PDF contains Embedded Files, which could potentially " "harmful."
            )
            return False

        # Check for suspicious keywords
        suspicious_keywords = ["eval", "exec", "system", "subprocess", "os.", "sys."]
        pdf_text = "".join(page.extract_text().lower() for page in reader.pages)
        if any(keyword in pdf_text for keyword in suspicious_keywords):
            logger.warning(
                f"PDF contains suspicious keywords: "
                f"{[kw for kw in suspicious_keywords if kw in pdf_text]}"
            )
            return False

        # !!! HAS TO BE MODIFIED !!!
        # Check for external links
        url_pattern = re.compile(r"https?://\S+|www\.\S+")
        if url_pattern.search(pdf_text):
            logger.warning(
                f"PDF contains external links, which could lead to "
                f"potentially harmful content.\nURL: "
                f"{url_pattern.search(pdf_text)}"
            )
            return False

        logger.info("PDF file validated successfully.")
        return True
    except Exception as e:
        logger.warning(f"Failed to validate PDF file: {e}")
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
        # Read the file content
        file_content = uploaded_file.read()
        uploaded_file.seek(0)

        # Check if it's a valid ZIP file
        if not zipfile.is_zipfile(io.BytesIO(file_content)):
            logger.warning(f"Not a valid ZIP file")
            return False

        # Open the DOCX file using python-docx
        doc = docx.Document(io.BytesIO(file_content))

        # Check for macros (which may be potentially harmful)
        zip_file = zipfile.ZipFile(io.BytesIO(file_content))
        if "word/vbaProject.bin" in zip_file.namelist():
            logger.warning(
                "DOCX file contains macros, which could be potentially " "harmful"
            )
            return False

        # Check for external links
        for rel in doc.part.rels.values():
            if rel.reltype == docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK:
                logger.warning(
                    "DOCX file contains external links, which could be "
                    "potentially harmful"
                )
                return False

        # Check for embedded objects
        if any("word/embeddings" in name for name in zip_file.namelist()):
            logger.warning(
                "DOCX file contains embedded objects, which could be "
                "potentially harmful"
            )
            return False

        # Check document content for potential malicious elements
        full_text = "\n".join(paragraph.text for paragraph in doc.paragraphs)

        # Check for potential script injection
        if re.search(r"<script|javascript:|data:>", full_text, re.IGNORECASE):
            logger.warning("DOCX file contains potential script injection")
            return False

        # Check for suspicious keywords
        suspicious_keywords = ["cmd", "powershell", "exec", "system", "eval"]
        if any(keyword in full_text.lower() for keyword in suspicious_keywords):
            logger.warning(
                f"DOCX file contains suspicious keywords: "
                f"{[kw for kw in suspicious_keywords if kw in full_text.lower()]}"
            )
            return False

        # Check file size (arbitary limit 10MB)
        if len(file_content) > 10 * 1024 * 1024:
            logger.warning("DOCX file is suspiciously large")
            return False

        logger.info("DOCX file validated successfully")
        return True
    except docx.opc.exceptions.PackageNotFoundError as e:
        logger.warning(f"Not a valid DOCX file: {e}")
        return False
    except Exception as e:
        logger.error(f"Error processing DOCX file: {e}")
        return False


def is_valid_doc(uploaded_file):
    """Checks if an uploaded file is a valid .doc document.

    Args:
        uploaded_file (FileStorage): The Flask uploaded file object.

    Returns:
        bool: True if the file is a valid .doc document, False otherwise.
    """
    logger.info(f"***'is_valid_doc' was triggered***")
    logger.info("Validating DOC file...")

    try:
        # Create a temporary file
        with (tempfile.NamedTemporaryFile(delete=True) as temp_file):
            # Read the uploaded file in chunks and write to the temporary file
            for chunk in uploaded_file.stream:
                temp_file.write(chunk)

            temp_file.flush()
            temp_file_name = temp_file.name

            ole = olefile.OleFileIO(temp_file_name)

            # Check if it's a Word document
            if not ole.exists("WordDocument"):
                logger.warning(
                    "File is not a valid DOC file (missing 'WordDocument' " "stream)"
                )
                ole.close()
                return False

            # root = ole.root
            # logger.info(f"'root': {root}")

            # Check for macros
            if (
                ole.exists("Macros")
                or ole.exists("_VBA_PROJECT_CUR")
                or ole.exists("VBA")
            ):
                logger.warning("Document contains macros. Potential security risk.")
                ole.close()
                return False

            # Check for external links
            if ole.exists("\\1Table"):
                table_stream = ole.openstream("\\1Table")
                table_data = table_stream.read()
                if (
                    b"HTTP://" in table_data.upper()
                    or b"HTTPS://" in table_data.upper()
                ):
                    logger.warning(
                        "Document contains external links. Potential " "security risk."
                    )
                    ole.close()
                    return False

            # Check for embedded objects
            if ole.exists("ObjectPool"):
                logger.warning(
                    "Document contains embedded objects. Potential security " "risk."
                )
                ole.close()
                return False

            # Check document content for potential malicious elements
            word_stream = ole.openstream("WordDocument")
            word_data = word_stream.read()

            # Check Word document for potential script injection
            if re.search(b"<script|javascript:|data:", word_data, re.IGNORECASE):
                logger.warning("DOC file contains potential script injection")
                ole.close()
                return False

            # Check for suspicious keywords
            suspicious_keywords = [b"cmd", b"powershell", b"exec", b"system", b"eval"]
            if any(keyword in word_data.lower() for keyword in suspicious_keywords):
                logger.warning("DOC file contains suspicious keywords")
                ole.close()
                return False

            # Check file size (arbitrary limit of 10MB)
            if os.path.getsize(temp_file.name) > 10 * 1024 * 1024:
                logger.warning("DOC file is suspiciously large")
                return False

            logger.info("DOC file validated successfully")
            ole.close()
            return True
    except Exception as e:
        logger.warning(f"Error processing DOC file: {e}")
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

    file_extension = uploaded_file.filename.split(".")[-1].lower()
    logger.info(f"'file_extension': {file_extension}")

    stream = uploaded_file.stream
    mime = magic.Magic()
    file_type_description = mime.from_buffer(stream.read(4096))
    stream.seek(0)
    logger.info(f"'file_type_description': {file_type_description}")

    match file_extension:
        case "docx":
            logger.info("Uploaded file was recognized as '.docx'.")
            return is_valid_docx(uploaded_file)
        case "pdf":
            logger.info("Uploaded file was recognized as '.pdf'.")
            return is_valid_pdf(uploaded_file)
        case "doc":
            logger.info("Uploaded file was recognized as '.doc'.")
            return is_valid_doc(uploaded_file)
        case _:
            logger.warning(
                f"Unsupported file type: "
                f"{file_type_description}\n'file_extension': {file_extension}"
            )
            return False


def path_secure(origin_file_path, file_key):
    """Secures the destination path for an uploaded file.

    Determines the appropriate subdirectory ('images' or 'files') based on
    file type and constructs a safe, sanitized filename.

    Args:
        origin_file_path (str): The original file path provided by the user.
        file_key (str): Key in the 'request.files' dictionary ('image' or
        'file').

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

    dest_dir = origin_file_path.split("/")[-2]
    logger.info(f"'dest_dir': {dest_dir}")
    if dest_dir not in ["images", "files"]:
        return Response("Directory not allowed", status=403)

    if is_valid_image(uploaded_file):
        allowed_path = os.path.join(app.config["MEDIA_FILES_DEST"], "images")
        logger.info(f"'allowed_path': {allowed_path}")
    elif is_valid_file(uploaded_file):
        allowed_path = os.path.join(app.config["MEDIA_FILES_DEST"], "files")
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
    file_extension = origin_file_path.split(".")[-1]
    logger.info(f"'file_extension': {file_extension}")

    if (
        file_extension not in ALLOWED_EXTENSIONS["image"]
        and file_extension not in ALLOWED_EXTENSIONS["document"]
    ):
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

    parts = req_abs_file_path.split("/")
    logger.info(f"directory: {'/'.join(parts[:-1])}")
    return "/".join(parts[:-1])


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

    req_abs_file_path = os.path.abspath(
        os.path.normpath(os.path.join(app.config["MEDIA_FILES_DEST"], origin_file_path))
    )
    logger.info(f"'req_abs_file_path': {req_abs_file_path}")

    media_abs_path = os.path.abspath(app.config["MEDIA_FILES_DEST"])
    logger.info(f"'media_abs_path': {media_abs_path}")

    allowed_dirs = [
        os.path.join(media_abs_path, directory) for directory in ALLOWED_DIRECTORIES
    ]
    logger.info(f"'allowed_dirs': {allowed_dirs}")

    req_dir = get_request_directory(req_abs_file_path)
    logger.info(f"'req_dir': {req_dir}")

    if os.path.exists(req_dir) and req_abs_file_path.startswith(media_abs_path):
        if req_dir in allowed_dirs:
            return True
    logger.warning(f"'req_abs_file_path': {req_abs_file_path}")
    logger.warning(f"!!! 'is_valid_file_path' FAILED !!!")
    return False


def allowed_path_and_extension(origin_file_path):
    """Checks if a file path is valid and has an allowed extension.

    Performs the following validations:
        *  The file path must be valid according to security and location
        constraints.
           (`is_valid_file_path` check).
        *  The file must have a supported file extension (
        `get_file_extension` check).

    Args:
        origin_file_path (str): The relative file path provided in the request.

    Returns:
        bool: True if the path is valid and the extension is allowed,
        False otherwise.
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
        Response:  If no suitable file is found in the request or the file
        size is too large.
    """
    logger.info("*** 'handle_upload' was triggered ***")
    logger.info(f"'origin_file_path': {origin_file_path}")
    logger.info(f"'request.files': {request.files}")

    if "image" not in request.files and "file" not in request.files:
        # logger.warning("'file' not in 'request.files'")
        logger.warning(f"'request.files': {request.files}")
        return Response("No file part", status=400)

    file_key = "image" if "image" in request.files else "file"
    try:
        uploaded_file = request.files[file_key]
        logger.info(f"'uploaded_file': {uploaded_file}")

        if uploaded_file.filename == "":
            logger.warning("uploaded_file.filename == ''")
            return Response("Empty filename", status=400)

        try:
            if allowed_path_and_extension(origin_file_path):
                logger.info("passed 'if allowed_path_and_extension(origin_file_path)'")
                secured_path = path_secure(origin_file_path, file_key)
                logger.info(f"'secured_path': {secured_path}")

                with open(secured_path, "wb") as destination_file:
                    uploaded_file.save(destination_file)
                os.chmod(secured_path, 0o755)
                logger.info("SUCCESS")
                return True
            else:
                logger.warning("!!! 'allowed_path_and_extension' failed !!!")
                return False
        except Exception as e:
            logger.info(f"Exception: {e}")
            logger.warning(f"!!! 'handle_upload' failed !!!")
            return False
    except Exception as e:
        logger.info(f"Exception: {e}")
        return False


@app.route("/media/<path:origin_file_path>", methods=["POST"])
@check_api_key
def upload_file(origin_file_path):
    """Handles file upload requests.

    Performs the following:
        * Logs the request.
        * Delegates the upload process to the `handle_upload` function.
        * Returns an appropriate response (success or error) based on the
        result of `handle_upload`.

    Args:
        origin_file_path (str): The relative file path extracted from the URL.
    """
    logger.info("*** 'upload_file' was triggered ***")
    logger.info("'POST' method detected")
    logger.info(f"'origin_file_path': {origin_file_path}")

    if handle_upload(origin_file_path):
        return Response("OK", status=200)
    return Response("Error uploading file", status=501)


if __name__ == "__main__":
    app.run()
