from typing import Union
from validators.image_validator import ImageValidator
from validators.doc_validator import DOCValidator
from validators.docx_validator import DOCXValidator
from validators.pdf_validator import PDFValidator
from config.validation_config import FileValidationConfig
from extensions.logger import logger


class ValidatorFactory:
    _validators = {
        "image": {
            "jpeg": ImageValidator,
            "jpg": ImageValidator,
            "png": ImageValidator,
            "gif": ImageValidator,
        },
        "doc": {"doc": DOCValidator},
        "docx": {"docx": DOCXValidator},
        "pdf": {"pdf": PDFValidator},
    }

    @classmethod
    def get_validator(
        cls, file_extension: str
    ) -> Union[DOCValidator, DOCXValidator, ImageValidator, PDFValidator]:
        """
        Gets the appropriate validator for the given file extension.

        Args:
            file_extension: The file extension for which to get the validator.

        Returns:
            Union[DOCValidator, DOCXValidator, ImageValidator, PDFValidator]: The validator instance for the given extension.

        Raises:
            ValueError: If the file extension is not allowed or if there is no validator available for the file extension.
        """
        file_extension = file_extension.lower()

        if not FileValidationConfig.is_extension_allowed(file_extension):
            raise ValueError(f"File extension not allowed: {file_extension}")

        validator_type = FileValidationConfig.get_validator_type(file_extension)
        logger.info(f"Validator type: {validator_type}")

        validator_dict = cls._validators.get(validator_type, {})
        logger.info(f"Validator dict: {validator_dict}")

        validator_class = cls._validators.get(validator_type, {}).get(file_extension)
        logger.info(f"Validator class: {validator_class}")

        if validator_class is None:
            raise ValueError(
                f"No validator available for file extension: {file_extension}"
            )

        return validator_class()
