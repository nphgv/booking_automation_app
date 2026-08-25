import re


# =========================================================
# HELPERS
# =========================================================

def clean_text(text):
    if not text:
        return ""
    return text.strip()


def clean_value(value):
    if not value:
        return ""

    value = value.strip()

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip(" :;,-")


def extract_number(value):
    if not value:
        return None

    value = value.strip()

    # 24,500 hoặc 24.500 => 24500
    if re.match(
        r"^\d{1,3}([,.]\d{3})+$",
        value
    ):
        value = (
            value
            .replace(",", "")
            .replace(".", "")
        )

    else:
        value = value.replace(
            ",",
            "."
        )

    try:
        return float(value)

    except ValueError:
        return None


def find_first(text, patterns):

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE | re.MULTILINE
        )

        if match:

            return clean_value(
                match.group(1)
            )

    return ""


# =========================================================
# CARRIER
# =========================================================

def detect_carrier(text):

    text_lower = text.lower()

    carriers = {

        "MAERSK": [
            "maersk",
            "mearsk"
        ],

        "CMA CGM": [
            "cma cgm",
            "cmacgm"
        ],

        "EVERGREEN": [
            "evergreen",
            "evergreen line"
        ],

        "ONE": [
            "ocean network express",
            "one line"
        ],

        "MSC": [
            "msc",
            "mediterranean shipping"
        ],

        "COSCO": [
            "cosco"
        ],

        "OOCL": [
            "oocl"
        ],

        "HAPAG-LLOYD": [
            "hapag",
            "hapag-lloyd"
        ],

        "YANG MING": [
            "yang ming",
            "yangming"
        ]
    }

    for carrier, keywords in carriers.items():

        for keyword in keywords:

            if keyword in text_lower:
                return carrier

    return ""


# =========================================================
# BOOKING ACCOUNT
# =========================================================

def extract_booking_account(text):

    text_lower = text.lower()

    customer_keywords = [
        "customer account",
        "client account",
        "account khách",
        "account khach",
        "acc khách",
        "acc khach",
        "tài khoản khách",
        "tai khoan khach"
    ]

    company_keywords = [
        "company account",
        "our account",
        "account công ty",
        "account cong ty",
        "acc công ty",
        "acc cong ty",
        "tài khoản công ty",
        "tai khoan cong ty",
        "book bằng account công ty",
        "booking bằng account công ty"
    ]

    for keyword in customer_keywords:

        if keyword in text_lower:
            return "CUSTOMER"

    for keyword in company_keywords:

        if keyword in text_lower:
            return "COMPANY"

    return ""


# =========================================================
# CUSTOMER
# =========================================================

def extract_customer_name(text):

    return find_first(
        text,
        [
            r"khách\s*hàng\s*[:\-]\s*([^\n\r]+)",
            r"customer\s*[:\-]\s*([^\n\r]+)"
        ]
    )


def extract_customer_email(text):

    return find_first(
        text,
        [
            r"(?:email\s*liên\s*hệ|email|mail)"
            r"\s*[:\-]\s*"
            r"([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})"
        ]
    )


# =========================================================
# PRODUCT
# =========================================================

def extract_product(text):

    return find_first(
        text,
        [
            r"tên\s*hàng\s*[:\-]\s*([^\n\r]+)",
            r"commodity\s*[:\-]\s*([^\n\r]+)",
            r"product\s*[:\-]\s*([^\n\r]+)",
            r"cargo\s*[:\-]\s*([^\n\r]+)"
        ]
    )


def extract_product_description(text):

    value = find_first(
        text,
        [
            r"mô\s*tả\s*hàng\s*[:\-]\s*([^\n\r]+)",
            r"cargo\s*description\s*[:\-]\s*([^\n\r]+)",
            r"description\s*[:\-]\s*([^\n\r]+)"
        ]
    )

    if value:
        return value

    return text.strip()


# =========================================================
# HS CODE
# =========================================================

def extract_hs_code(text):

    return find_first(
        text,
        [
            r"hs\s*code\s*[:\-]?\s*([0-9.\-]{4,15})",
            r"hscode\s*[:\-]?\s*([0-9.\-]{4,15})",
            r"\bhs\s*[:\-]?\s*([0-9.\-]{4,15})"
        ]
    )


# =========================================================
# WEIGHT
# =========================================================

def extract_weight(text):

    patterns = [
        r"(?:trọng\s*lượng\s*hàng|trọng\s*lượng|gross\s*weight|cargo\s*weight|weight|gwt|gw)"
        r"\s*[:\-]?\s*"
        r"([\d,.]+)"
        r"\s*(kg|kgs|mt|ton|tons)?",

        r"([\d,.]+)\s*(kg|kgs|mt|ton|tons)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            number = extract_number(
                match.group(1)
            )

            if number is None:
                continue

            unit = ""

            if len(match.groups()) >= 2:
                unit = (
                    match.group(2)
                    or ""
                )

            unit = unit.lower()

            if unit in [
                "mt",
                "ton",
                "tons"
            ]:
                number *= 1000

            return number

    return None


# =========================================================
# VOLUME
# =========================================================

def extract_volume(text):

    patterns = [
        r"(?:thể\s*tích|the\s*tich|volume|measurement|cbm)"
        r"\s*[:\-]?\s*"
        r"([\d,.]+)"
        r"\s*(?:cbm|m3|m³)?",

        r"([\d,.]+)\s*(?:cbm|m3|m³)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            return extract_number(
                match.group(1)
            )

    return None


# =========================================================
# CONTAINER
# =========================================================

def extract_container_quantity(text):

    return find_first(
        text,
        [
            r"số\s*lượng\s*container\s*[:\-]\s*([^\n\r]+)",
            r"container\s*quantity\s*[:\-]\s*([^\n\r]+)",
            r"qty\s*/?\s*type\s*[:\-]?\s*([^\n\r]+)"
        ]
    )


# =========================================================
# PORTS
# =========================================================

def extract_port_of_receipt(text):

    return find_first(
        text,
        [
            r"port\s*of\s*receipt\s*[:\-]\s*([^\n\r]+)",
            r"por\s*[:\-]\s*([^\n\r]+)"
        ]
    )


def extract_port_of_loading(text):

    return find_first(
        text,
        [
            r"port\s*of\s*loading\s*(?:\(pol\))?\s*[:\-]\s*([^\n\r]+)",
            r"\bpol\s*[:\-]\s*([^\n\r]+)"
        ]
    )


def extract_port_of_discharge(text):

    return find_first(
        text,
        [
            r"port\s*of\s*discharge\s*(?:\(pod\))?\s*[:\-]\s*([^\n\r]+)",
            r"\bpod\s*[:\-]\s*([^\n\r]+)"
        ]
    )


# =========================================================
# SHIPPER / CONSIGNEE
# =========================================================

def extract_shipper(text):

    return find_first(
        text,
        [
            r"shipper\s*[:\-]\s*([^\n\r]+)"
        ]
    )


def extract_consignee(text):

    return find_first(
        text,
        [
            r"consignee\s*[:\-]\s*([^\n\r]+)"
        ]
    )


def extract_notify_party(text):

    return find_first(
        text,
        [
            r"notify\s*party\s*[:\-]\s*([^\n\r]+)"
        ]
    )


# =========================================================
# IMO / UN
# =========================================================

def extract_imo_class(text):

    return find_first(
        text,
        [
            r"imo\s*class\s*[:\-]\s*([0-9.]+)"
        ]
    )


def extract_un_no(text):

    return find_first(
        text,
        [
            r"un\s*(?:no|number)\s*[:\-]\s*([0-9]{4})"
        ]
    )


# =========================================================
# PROPER SHIPPING NAME
# =========================================================

def extract_proper_shipping_name(text):

    return find_first(
        text,
        [
            r"proper\s*shipping\s*name\s*[:\-]\s*([^\n\r]+)"
        ]
    )


# =========================================================
# ETD
# =========================================================

def extract_etd(text):

    return find_first(
        text,
        [
            r"(?:dự\s*kiến\s*)?etd\s*[:\-]\s*([^\n\r]+)"
        ]
    )


# =========================================================
# MAIN PARSER
# =========================================================

def parse_email(email_text):

    email_text = clean_text(
        email_text
    )

    result = {
        "customer_name":
            extract_customer_name(
                email_text
            ),

        "customer_email":
            extract_customer_email(
                email_text
            ),

        "carrier_name":
            detect_carrier(
                email_text
            ),

        "booking_account":
            extract_booking_account(
                email_text
            ),

        "product_name":
            extract_product(
                email_text
            ),

        "product_description":
            extract_product_description(
                email_text
            ),

        "hs_code":
            extract_hs_code(
                email_text
            ),

        "cargo_weight":
            extract_weight(
                email_text
            ),

        "cargo_volume":
            extract_volume(
                email_text
            ),

        "container_quantity":
            extract_container_quantity(
                email_text
            ),

        "port_of_receipt":
            extract_port_of_receipt(
                email_text
            ),

        "port_of_loading":
            extract_port_of_loading(
                email_text
            ),

        "port_of_discharge":
            extract_port_of_discharge(
                email_text
            ),

        "shipper":
            extract_shipper(
                email_text
            ),

        "consignee":
            extract_consignee(
                email_text
            ),

        "notify_party":
            extract_notify_party(
                email_text
            ),

        "imo_class":
            extract_imo_class(
                email_text
            ),

        "un_no":
            extract_un_no(
                email_text
            ),

        "proper_shipping_name":
            extract_proper_shipping_name(
                email_text
            ),

        "etd_date":
            extract_etd(
                email_text
            )
    }

    return result


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    sample_email = """
    Subject: Booking request HCM - Surabaya / Evergreen

    Chào team,

    Nhờ team hỗ trợ book lô hàng bên dưới giúp mình nhé.

    Khách hàng: BAYER VIETNAM LTD.
    Email liên hệ: logistics@bayer-example.com

    Hãng tàu: EVERGREEN
    Booking bằng account công ty.

    Tên hàng: CAPRENO SCS547 100X100ML BOT
    Mô tả hàng: Thuốc bảo vệ thực vật dạng chai

    HS Code: 380893

    Trọng lượng hàng: 18,500 KG
    Thể tích: 32.5 CBM

    Số lượng container: 1 x 20GP

    Port of Receipt: HO CHI MINH
    Port of Loading (POL): HO CHI MINH
    Port of Discharge (POD): SURABAYA, INDONESIA

    Shipper: BAYER VIETNAM LTD.
    Consignee: ABC TRADING INDONESIA
    Notify Party: SAME AS CONSIGNEE

    IMO Class: 9
    UN No: 3082

    Proper Shipping Name:
    ENVIRONMENTALLY HAZARDOUS SUBSTANCE, LIQUID, N.O.S.

    Dự kiến ETD: 22/08/2026
    """

    parsed = parse_email(
        sample_email
    )

    print()
    print(
        "PARSED EMAIL"
    )

    print(
        "=" * 60
    )

    for key, value in parsed.items():

        print(
            f"{key}: {value}"
        )