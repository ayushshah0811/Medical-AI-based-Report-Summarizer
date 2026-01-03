import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from pdfminer.high_level import extract_text as pdfminer_extract

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


MAX_PAGES_TO_PROCESS = 6
MIN_TEXT_LENGTH = 500  # heuristic threshold

def extract_text(filepath):
    """
    1. Try fast text extraction using pdfminer
    2. If text is sufficient, return it
    3. Else fallback to OCR
    """

    # -------- FAST PATH (pdfminer) --------
    try:
        text = pdfminer_extract(filepath)
        if text and len(text.strip()) > MIN_TEXT_LENGTH:
            print("✅ Using pdfminer (fast path)")
            return clean_text(text)
    except Exception as e:
        print("⚠️ pdfminer failed, falling back to OCR:", e)

    # -------- SLOW PATH (OCR fallback) --------
    print("🐢 Falling back to OCR")

    images = convert_from_path(filepath)
    extracted_text = []

    for page in images[:MAX_PAGES_TO_PROCESS]:
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

    return clean_text("\n".join(extracted_text))


def clean_text(text):
    """
    Light cleanup to reduce LLM load
    """
    lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 2]
    return "\n".join(lines)
 