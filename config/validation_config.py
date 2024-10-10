from typing import List, Set, Union, Dict
from dataclasses import dataclass, field


def default_suspicious_keywords() -> List[str]:
    return ["eval", "exec", "system", "subprocess", "os.", "sys."]


def default_allowed_png_chunks() -> List[bytes]:
    return [
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
    ]


@dataclass
class BaseValidationConfig:
    suspicious_keywords: List[str] = field(default_factory=default_suspicious_keywords)
    # allowed_png_chunks: List[str] = field(default_factory=lambda: [
    #     "eval",
    #     "exec",
    #     "system",
    #     "subprocess",
    #     "os.",
    #     "sys."
    # ])
    max_file_size: int = 10 * 1024 * 1024  # 10 MB
    allowed_extensions: Set[str] = field(default_factory=set)


@dataclass
class ImageValidationConfig(BaseValidationConfig):
    allowed_extensions: Set[str] = field(
        default_factory=lambda: {"jpeg", "jpg", "png", "gif"}
    )
    allowed_png_chunks: List[str] = field(default_factory=default_allowed_png_chunks)
    max_dimensions: tuple = (8000, 8000)


@dataclass
class DocumentValidationConfig(BaseValidationConfig):
    max_pages: int = 100


@dataclass
class PDFValidationConfig(BaseValidationConfig):
    allowed_extensions: Set[str] = field(default_factory=lambda: {"pdf"})
    allowed_versions: List[str] = field(
        default_factory=lambda: ["1.4", "1.5", "1.6", "1.7"]
    )


@dataclass
class DOCValidationConfig(DocumentValidationConfig):
    allowed_extensions: Set[str] = field(default_factory=lambda: {"doc"})
    suspicious_keywords: List[bytes] = field(
        default_factory=lambda: [b"cmd", b"powershell", b"exec", b"system", b"eval"]
    )
    macros: List[bytes] = field(
        default_factory=lambda: ["Macros", "_VBA_PROJECT_CUR", "VBA"]
    )


@dataclass
class DOCXValidationConfig(DocumentValidationConfig):
    allowed_extensions: Set[str] = field(default_factory=lambda: {"docx"})
    suspicious_keywords: List[str] = field(
        default_factory=lambda: list(
            set(
                DocumentValidationConfig().suspicious_keywords
                + ["cmd", "powershell", "exec", "system", "eval"]
            )
        )
    )


ValidatorConfigType = Union[
    ImageValidationConfig,
    PDFValidationConfig,
    DOCValidationConfig,
    DocumentValidationConfig,
    BaseValidationConfig,
]


class FileValidationConfig:
    CONFIGS: Dict[str, ValidatorConfigType] = {
        "image": ImageValidationConfig(),
        "pdf": PDFValidationConfig(),
        "doc": DOCValidationConfig(),
        "docx": DOCXValidationConfig(),
    }

    @classmethod
    def get_config(cls, file_type: str) -> ValidatorConfigType:
        return cls.CONFIGS.get(file_type.lower(), BaseValidationConfig())

    @classmethod
    def get_validator_type(cls, file_extension: str) -> str:
        for validator_type, config in cls.CONFIGS.items():
            if file_extension in config.allowed_extensions:
                return validator_type
        return "unknown"

    @classmethod
    def is_extension_allowed(cls, file_extension: str) -> bool:
        return any(
            file_extension.lower() in config.allowed_extensions
            for config in cls.CONFIGS.values()
        )
