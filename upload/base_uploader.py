from abc import ABC, abstractmethod
from pathlib import Path

class BaseUploader(ABC):
    """
    Абстрактный класс для всех загрузчиков.
    Обязует реализовать метод upload.
    """

    def __init__(self, profile_path: str | None = None):
        """
        :param profile_path: путь к Selenium-профилю (если используется)
        """
        self.profile_path = profile_path

    @abstractmethod
    def upload(self,
               video_file: Path | str,
               title: str,
               description: str,
               tags: list[str] | None = None,
               thumbnail: str | None = None) -> dict:
        """
        Метод загрузки, который должен быть реализован в наследниках.

        :return: словарь с результатом загрузки
        """
        raise NotImplementedError
