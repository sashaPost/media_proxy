from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.app_config import AppConfig
from routes.file_routes import file_router
from routes.health_check import health_router
import os


def initialize_directories(config: AppConfig):
    os.makedirs(config.MEDIA_FILES_DEST, exist_ok=True)
    for directory in config.ALLOWED_DIRECTORIES:
        os.makedirs(os.path.join(config.MEDIA_FILES_DEST, directory), exist_ok=True)


def create_app() -> FastAPI:
    app = FastAPI(title="Media Proxy API")
    config = AppConfig()

    initialize_directories(config)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(file_router, prefix="/media")
    app.include_router(health_router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
