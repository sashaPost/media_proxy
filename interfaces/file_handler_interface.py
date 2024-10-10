from abc import ABC, abstractmethod
from flask import Response
from typing import Union, Tuple


class IFileHandler(ABC):
    @abstractmethod
    def handle_get_request(
        self, file_path: str
    ) -> Union[Response, Tuple[Response, int]]:
        pass

    @abstractmethod
    def handle_post_request(
        self, file_path: str
    ) -> Union[Response, Tuple[Response, int]]:
        pass
