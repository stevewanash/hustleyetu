import requests
import io
import re
import os
import platform
import urllib3
from PIL import Image
import pytesseract
import pdfplumber

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure Tesseract path for Windows
if platform.system() == "Windows":
    # Default common paths for Tesseract on Windows
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'
    ]
    for p in possible_paths:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            break

def pdf_page_to_image(page, scale=300):
    """
    Renders a pdfplumber page object to a PIL Image using .to_image().
    """
    img_wrapper = page.to_image(resolution=scale)
    try:
        return img_wrapper.original
    except AttributeError:
        return img_wrapper

async def extract_text_from_pdf(url: str, max_pages: int = 50) -> str:
    """
    Downloads PDF and extracts text, prioritizing OCR if initial digital extraction fails.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/pdf',
    }
    extracted_text = ""
    
    try:
        response = requests.get(url, headers=headers, stream=True, allow_redirects=True, timeout=30, verify=False)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '').lower()
        if 'application/pdf' not in content_type:
            raise ValueError(f"Content received was not PDF ({content_type}).")

        pdf_stream = io.BytesIO(response.content)

        with pdfplumber.open(pdf_stream) as pdf:
            pages_to_read = min(len(pdf.pages), max_pages)

            for i in range(pages_to_read):
                page = pdf.pages[i]
                
                # 1. Attempt basic extraction first (fastest method)
                page_text = page.extract_text()
                
                if page_text and len(page_text.strip()) > 50:
                    extracted_text += page_text.strip() + "\n"
                else:
                    # 2. Failure: Run OCR on the page image (slow, but works on scans)
                    page_img = pdf_page_to_image(page)
                    ocr_text = pytesseract.image_to_string(page_img)
                    
                    if ocr_text:
                        extracted_text += ocr_text.strip() + "\n"

        if not extracted_text:
            raise ValueError("Downloaded PDF, but neither digital extraction nor OCR found text.")

        return extracted_text.strip()

    except requests.exceptions.HTTPError as e:
        raise ValueError(f"HTTP Error during download: {e}")
    except Exception as e:
        raise ValueError(f"Critical PDF Processing Error: {e}")
