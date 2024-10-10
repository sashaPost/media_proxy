from abc import ABC, abstractmethod
from werkzeug.datastructures.file_storage import FileStorage


class IFileValidator(ABC):
    @abstractmethod
    def is_valid(self, uploaded_file: "FileStorage") -> bool:
        pass
