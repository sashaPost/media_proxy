from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Annotated
from config.app_config import AppConfig
from utils.file_route_handler import FileRouteHandler
from middleware.auth import create_auth_middleware


file_router = APIRouter()


config = AppConfig()


auth = create_auth_middleware(config)


async def get_file_handler():
    return FileRouteHandler()


@file_router.get("/{file_path:path}")
async def handle_get_request(
    file_path: str, file_handler: Annotated[FileRouteHandler, Depends(get_file_handler)]
):
    try:
        return await file_handler.handle_get_request(file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@file_router.post("/{origin_file_path:path}")
async def handle_post_request(
    origin_file_path: str,
    file_handler: Annotated[FileRouteHandler, Depends(get_file_handler)],
    _: Annotated[bool, Depends(auth.verify_api_key)],
    file: UploadFile = File(...),
):
    try:
        return await file_handler.handle_post_request(origin_file_path, file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
