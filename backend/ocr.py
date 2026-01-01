import pytesseract
from pdf2image import convert_from_path
from PIL import Image

def extract_text_from_image(image_path):
    try:
        return pytesseract.image_to_string(Image.open(image_path))
    except:
        return ""

def extract_text_from_pdf(pdf_path):
    try:
        pages = convert_from_path(pdf_path, dpi=120)  # ⚡ optimized
        text = ""
        for page in pages:
            text += pytesseract.image_to_string(page, config="--psm 6") + "\n"
        return text
    except:
        return ""

def extract_text(filepath):
    ext = filepath.split(".")[-1].lower()
    if ext in ["png", "jpg", "jpeg"]:
        return extract_text_from_image(filepath)
    elif ext == "pdf":
        return extract_text_from_pdf(filepath)
    return ""
