import pytesseract
from pdf2image import convert_from_path
from PIL import Image

def extract_text_from_image(image_path):
    text = pytesseract.image_to_string(Image.open(image_path))
    return text

def extract_text_from_pdf(pdf_path):
    pages = convert_from_path(pdf_path)
    full_text = ""
    for page in pages:
        text = pytesseract.image_to_string(page, config="--psm 6")
        full_text += text + "\n"
    return full_text

def extract_text(filepath):
    ext = filepath.split(".")[-1].lower()

    if ext in ["png", "jpg", "jpeg"]:
        return extract_text_from_image(filepath)
    elif ext == "pdf":
        return extract_text_from_pdf(filepath)
    else:
        return ""
