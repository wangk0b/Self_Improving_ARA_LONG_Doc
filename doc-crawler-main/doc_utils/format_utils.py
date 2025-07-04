import os
from pathlib import Path
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pymupdf as fitz

from validation_schema import ValidationError, ValidationErrorType

    
def convert_to_images(file_path):
    if file_path.endswith('.pdf'):
        images = convert_from_path(file_path, dpi=72)
    else:
        return ValidationError(error_type=ValidationErrorType('unsupported_file_type'))
    return images 
    
def get_pdf_orientation(reader):
    try:
        first_page = reader.pages[1]  # Skip cover
    except IndexError:
        first_page = reader.pages[0]

    try:
        media_box = first_page.mediabox
        width = float(media_box.upper_right[0]) - float(media_box.lower_left[0])
        height = float(media_box.upper_right[1]) - float(media_box.lower_left[1])
        return "landscape" if width >= height else "portrait"
    except Exception:
        return "unknown"
    
    
def get_pdf_info(file_path):
    try:
        reader = PdfReader(str(file_path))
        orientation = get_pdf_orientation(reader)
        number_of_pages = len(reader.pages)
        del reader
        return {
            "orientation": orientation,
            "number_of_pages": number_of_pages
        }
        
    except Exception:
        return False          


def validate_and_extract_metadata(file_path, root_date=None):
    """
    Validates PDF file and extracts metadata from file path structure.
    
    Returns:
        dict: File metadata if valid, False if invalid/unreadable
    """
    if root_date:
        file_path = f'{root_date}/{file_path}'
        
    try:
        stat = file_path.stat()
        size = stat.st_size
        if size == 0:
            return ValidationError(error_type=ValidationErrorType('empty_file'))
        
    except OSError:
        #TODO: check if it's file not found error
        return ValidationError(error_type=ValidationErrorType('os_error'))

    parts = file_path.parts

    info = {}
    if file_path.suffix.lower() == '.pdf':
        info = get_pdf_info(file_path)
        if not info:
            return ValidationError(error_type=ValidationErrorType('pdf_processing_error'))
    else:
        return ValidationError(error_type=ValidationErrorType('unsupported_file_type'))
    
    file_metadata = {   "language": parts[-8],
                        "category": parts[-7],
                        "sub_category": parts[-6],
                        "format": parts[-5].lower().replace('.',''),
                        "download_date": "/".join(list(parts[-4:-1])),
                        "file_size": size,
                        "store_path": os.path.join(*parts[-9:]),  # Used to join with download logs
                    }
    file_metadata.update(info)
    
    return file_metadata
    

def read_file(file_path):
    """
    Reads the content of a file and returns it as bytes.
    """
    try:
        if not os.path.exists(file_path):
            print(f"File {file_path} does not exist.")
            return None
        
        if file_path.endswith('.pdf'):
            doc = fitz.open(file_path)
            pages_text = [page.get_text() for page in doc]
            return pages_text
        else:
            return ValidationError(error_type=ValidationErrorType('unsupported_file_type'))
                
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ValidationError(error_type=ValidationErrorType('os_error'))