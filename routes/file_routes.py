from http.client import HTTPException
from werkzeug.wrappers import Response as WerkzeugResponse
from flask import (
    Blueprint,
    current_app,
    Response,
    g,
)

from config.app_config import AppConfig
from middleware.auth import create_auth_middleware
from storage.local_storage import LocalFileSystemStorage
from utils.file_route_handler import FileRouteHandler
from typing import Tuple, Union
from validators.factory import ValidatorFactory


file_bp = Blueprint("file", __name__)


config = AppConfig()
auth = create_auth_middleware(config)


@file_bp.before_request
def init_file_handler() -> None:
    """
    Initializes the file handler before each request.
    The file handler is stored in `g` for use in routes.
    """
    g.file_handler = FileRouteHandler(
        config=config,
        storage_strategy=LocalFileSystemStorage(current_app.config["MEDIA_FILES_DEST"]),
        validator_factory=ValidatorFactory(),
    )


@file_bp.route("/media/<path:file_path>", methods=["GET"])
def handle_get_request(file_path: str) -> Union[Response, Tuple[Response, int]]:
    """
    Handles GET requests to retrieve files from the media directory.

    Args:
        file_path (str): The path to the requested file relative to the media directory.

    Returns:
        Union[Response, Tuple[Response, int]]: A Flask response object containing the
        requested file or an error message.
    """
    try:
        return g.file_handler.handle_get_request(file_path)
    except HTTPException as e:
        if isinstance(e.response, WerkzeugResponse):
            return e.response
        return str(e), e.code
    except Exception as e:
        current_app.logger.error(f"Error handling GET request: {str(e)}")
        return Response("Internal Server Error", status=500)


@file_bp.route("/media/<path:origin_file_path>", methods=["POST"])
@auth.check_api_key
def handle_post_request(origin_file_path: str) -> Union[Response, Tuple[Response, int]]:
    """
    Handles POST requests for uploading files to the media directory.

    Args:
        origin_file_path (str): The relative file path extracted from the URL,
                                intended for the uploaded file.

    Returns:
        Union[Response, Tuple[Response, int]]: A Flask response object indicating
        success (200 OK) or error during the upload process.
    """
    try:
        return g.file_handler.handle_post_request(origin_file_path)
    except HTTPException as e:
        if isinstance(e.response, WerkzeugResponse):
            return e.response
        return str(e), e.code
    except Exception as e:
        current_app.logger.error(f"Error handling POST request: {str(e)}")
        return Response("Internal Server Error", status=500)
