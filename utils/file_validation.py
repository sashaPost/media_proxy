from extensions.logger import logger
import magic
import io
from PyPDF2 import PdfReader
import re
import zipfile
import docx
import tempfile
from PIL import Image
import olefile
import os
import struct


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
