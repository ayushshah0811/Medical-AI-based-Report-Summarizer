from PIL import Image
import pytesseract
from pdfminer.high_level import extract_text as pdfminer_extract
from pdf2image import convert_from_path

def extract_text(filepath):
    ext = filepath.rsplit(".", 1)[1].lower()

    # -------- IMAGE FILES --------
    if ext in {"png", "jpg", "jpeg"}:
        image = Image.open(filepath).convert("L")
        image = image.resize(
            (image.width // 2, image.height // 2)
        )
        return pytesseract.image_to_string(
            image,
            config="--oem 1 --psm 6"
        )

    # -------- PDF FILES --------
    try:
        text = pdfminer_extract(filepath)
        if text and len(text.strip()) > 500:
            return clean_text(text)
    except Exception:
        pass

    # OCR fallback for scanned PDFs
    images = convert_from_path(filepath)
    extracted = []

    for page in images[:6]:
        page = page.convert("L")
        page = page.resize((page.width // 2, page.height // 2))
        extracted.append(
            pytesseract.image_to_string(
                page,
                config="--oem 1 --psm 6"
            )
        )

    return clean_text("\n".join(extracted))

def clean_text(text):
    """
    Light cleanup to reduce LLM load
    """
    lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 2]
    return "\n".join(lines)
 