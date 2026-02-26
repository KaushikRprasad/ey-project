import pytesseract
from PIL import Image
from django.conf import settings
import os

def extract_text_from_image(file_path):
    """
    Extract text from image or PDF using OCR.
    """
    try:
        text = pytesseract.image_to_string(Image.open(file_path))
        return text
    except Exception as e:
        return f"Error: {e}"
