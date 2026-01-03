import pytesseract
from pdf2image import convert_from_path
from PIL import Image

def extract_text_from_image(image_path):
    try:
        return pytesseract.image_to_string(Image.open(image_path))
    except:
        return ""

def extract_text_from_pdf(filepath):
    images = convert_from_path(filepath)
    extracted_text = []

    for page in images[:6]:
        page = page.convert("L")
        page = page.resize(
            (page.width // 2, page.height // 2)
        )

        extracted_text.append(
            pytesseract.image_to_string(
                page,
                config="--oem 1 --psm 6"
            )
        )

        del page

    return "\n".join(extracted_text)

def extract_text(filepath):
    ext = filepath.split(".")[-1].lower()
    if ext in ["png", "jpg", "jpeg"]:
        return extract_text_from_image(filepath)
    elif ext == "pdf":
        return extract_text_from_pdf(filepath)
    return ""
