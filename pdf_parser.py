import io

import fitz
import pytesseract

from PIL import Image, ImageEnhance, ImageFilter


# =========================================================
# SETTINGS
# =========================================================

MIN_NATIVE_TEXT_LENGTH = 80

OCR_DPI = 300


# =========================================================
# CLEAN TEXT
# =========================================================

def clean_text(text):

    if not text:
        return ""

    lines = []

    for line in text.splitlines():

        line = line.strip()

        if line:
            lines.append(line)

    return "\n".join(lines)


# =========================================================
# GET NATIVE TEXT
# =========================================================

def get_native_text(page):

    text = page.get_text(
        "text"
    )

    return clean_text(
        text
    )


# =========================================================
# SHOULD OCR?
# =========================================================

def should_use_ocr(native_text):

    if not native_text:
        return True

    compact = "".join(
        native_text.split()
    )

    return (
        len(compact)
        < MIN_NATIVE_TEXT_LENGTH
    )


# =========================================================
# PDF PAGE -> IMAGE
# =========================================================

def page_to_image(
    page,
    dpi=OCR_DPI
):

    zoom = dpi / 72

    matrix = fitz.Matrix(
        zoom,
        zoom
    )

    pix = page.get_pixmap(
        matrix=matrix,
        alpha=False
    )

    image_bytes = pix.tobytes(
        "png"
    )

    image = Image.open(
        io.BytesIO(
            image_bytes
        )
    )

    return image


# =========================================================
# PREPROCESS IMAGE
# =========================================================

def preprocess_image(image):

    # Grayscale
    image = image.convert(
        "L"
    )

    # Contrast
    enhancer = (
        ImageEnhance
        .Contrast(image)
    )

    image = enhancer.enhance(
        1.6
    )

    # Sharpen
    image = image.filter(
        ImageFilter.SHARPEN
    )

    return image


# =========================================================
# OCR PAGE
# =========================================================

def ocr_page(page):

    image = page_to_image(
        page
    )

    image = preprocess_image(
        image
    )

    text = (
        pytesseract
        .image_to_string(
            image,
            lang="eng",
            config="--oem 3 --psm 6"
        )
    )

    return clean_text(
        text
    )


# =========================================================
# UNIVERSAL PDF READER FROM BYTES
# =========================================================

def read_pdf_bytes(
    pdf_bytes,
    file_name="uploaded.pdf"
):

    """
    Đây là function app Streamlit sẽ sử dụng.

    pdf_bytes đến trực tiếp từ file uploader.

    Không cần người dùng copy PDF vào project.
    """

    document = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    pages_result = []

    full_text_parts = []

    native_pages = 0
    ocr_pages = 0

    try:

        total_pages = len(
            document
        )

        for index in range(
            total_pages
        ):

            page = document[
                index
            ]

            native_text = (
                get_native_text(
                    page
                )
            )

            # =============================================
            # SCAN -> OCR
            # =============================================

            if should_use_ocr(
                native_text
            ):

                page_text = (
                    ocr_page(
                        page
                    )
                )

                method = "OCR"

                ocr_pages += 1

            # =============================================
            # NORMAL PDF
            # =============================================

            else:

                page_text = (
                    native_text
                )

                method = "NATIVE"

                native_pages += 1


            pages_result.append(
                {
                    "page_number":
                        index + 1,

                    "method":
                        method,

                    "character_count":
                        len(
                            page_text
                        ),

                    "text":
                        page_text
                }
            )

            full_text_parts.append(
                page_text
            )

    finally:

        document.close()


    # =====================================================
    # DETECT DOCUMENT TYPE
    # =====================================================

    if (
        ocr_pages > 0
        and native_pages == 0
    ):

        document_type = (
            "SCAN"
        )

    elif (
        ocr_pages > 0
        and native_pages > 0
    ):

        document_type = (
            "HYBRID"
        )

    else:

        document_type = (
            "TEXT"
        )


    full_text = "\n\n".join(
        full_text_parts
    )


    return {

        "file_name":
            file_name,

        "document_type":
            document_type,

        "total_pages":
            len(
                pages_result
            ),

        "native_pages":
            native_pages,

        "ocr_pages":
            ocr_pages,

        "pages":
            pages_result,

        "full_text":
            full_text
    }