import fitz
from PIL import Image
import imagehash
import io
import os


HRDC_LOGO_PATH = "assets/hrdc_logo.png"
HRDC_HASH_THRESHOLD = 10  


_REF_HASH = None


def _get_ref_hash():
    global _REF_HASH

    if _REF_HASH is None:
        ref_img = Image.open(HRDC_LOGO_PATH).convert("RGBA")
        _REF_HASH = imagehash.phash(ref_img)

    return _REF_HASH


def detect_hrdc_logo(pdf_path):
    HRDC_HASH_THRESHOLD = 25

    ref_hash = _get_ref_hash()

    with fitz.open(pdf_path) as doc:
        for page in doc[:2]:
            images = page.get_images(full=True)

            for img in images:
                xref = img[0]
                base = doc.extract_image(xref)
                image_bytes = base["image"]

                try:
                    img_pil = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
                    img_hash = imagehash.phash(img_pil)
                    distance = abs(ref_hash - img_hash)


                    if distance <= HRDC_HASH_THRESHOLD:
                        return True
                except Exception:
                    continue
    return False

