from dataclasses import dataclass
from typing import Union, Optional
from enum import Enum

class ValidationErrorType(Enum):
    OS_ERROR = "os_error"
    FILE_NOT_FOUND = "file_not_found"
    EMPTY_FILE = "empty_file"
    UNSUPPORTED_FILE_TYPE = "unsupported_file_type"
    PDF_PROCESSING_ERROR = "pdf_processing_error"
    INVALID_PATH_STRUCTURE = "invalid_path_structure"

@dataclass
class ValidationError:
    error_type: ValidationErrorType
