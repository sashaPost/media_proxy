from abc import ABC, abstractmethod


class StorageStrategy(ABC):
    @abstractmethod
    def save_file(self, file_path: str, file_content: bytes) -> None:
        pass

    @abstractmethod
    def get_file(self, file_path: str) -> bytes:
        pass

    #
    # @abstractmethod
    # def make_full_path(self, file_path:str) -> str:
    #     pass
