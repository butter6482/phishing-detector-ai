from PIL import Image
import pytesseract
from io import BytesIO


def extract_text_from_image(raw: bytes, lang: str = "spa+eng") -> str:
    """Extract text from a JPG/PNG image buffer using Tesseract.

    lang: e.g., "spa+eng" for Spanish+English if installed.
    """
    img = Image.open(BytesIO(raw)).convert("RGB")
    # Optional light preprocessing:
    # img = img.resize((int(img.width*1.2), int(img.height*1.2)))
    text = pytesseract.image_to_string(img, lang=lang)
    return (text or "").strip()

