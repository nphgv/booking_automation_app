import re


# =========================================================
# HELPERS
# =========================================================

def clean_value(value):
    if not value:
        return ""

    value = value.strip()

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip(
        " :;,."
    )


def find_first(text, patterns):
    """
    Thử nhiều regex.
    Match được pattern đầu tiên thì trả kết quả.
    """

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
# DETECT CARRIER
# =========================================================

def detect_carrier(text):

    upper = text.upper()

    if (
        "EVERGREEN LINE" in upper
        or
        "EVERGREEN MARINE" in upper
    ):
        return "EVERGREEN"

    if "MAERSK" in upper:
        return "MAERSK"

    if "CMA CGM" in upper:
        return "CMA CGM"

    if (
        "OCEAN NETWORK EXPRESS"
        in upper
    ):
        return "ONE"

    if (
        "MEDITERRANEAN SHIPPING"
        in upper
    ):
        return "MSC"

    if "COSCO" in upper:
        return "COSCO"

    if "OOCL" in upper:
        return "OOCL"

    if "HAPAG-LLOYD" in upper:
        return "HAPAG-LLOYD"

    return "UNKNOWN"


# =========================================================
# GENERIC FIELDS
# =========================================================

def extract_booking_no(text):

    return find_first(
        text,
        [
            r"BOOKING\s*NO\.?\s*[:\-]?\s*([A-Z0-9\-]+)",
            r"BOOKING\s*NUMBER\s*[:\-]?\s*([A-Z0-9\-]+)"
        ]
    )


def extract_vessel_voyage(text):

    return find_first(
        text,
        [
            r"VESSEL\s*/\s*VOYAGE\s*[\"':\-]*\s*([^\n\r]+)",
            r"VESSEL\s+VOYAGE\s*[:\-]?\s*([^\n\r]+)"
        ]
    )


def extract_port_of_receipt(text):

    return find_first(
        text,
        [
            r"PORT\s+OF\s+RECEIPT[^\n:]*[:]\s*([^\n\r,]+)",
        ]
    )


def extract_port_of_loading(text):

    return find_first(
        text,
        [
            r"PORT\s+OF\s+LOADING\s*[:]\s*([^\n\r,]+)"
        ]
    )


def extract_port_of_discharge(text):

    return find_first(
        text,
        [
            r"PORT\s+OF\s+DISCHARGE[^\n:]*[:]\s*([^\n\r]+)"
        ]
    )


# =========================================================
# CUT OFF
# =========================================================

def extract_cy_cutoff(text):

    return find_first(
        text,
        [
            r"CUT\s*OFF\s*DATE\s*/?\s*TIME\s*[:]\s*([^\n\r]+)",
            r"CY\s*CUT\s*OFF[^\n:]*[:]\s*([^\n\r]+)"
        ]
    )


def extract_vgm_cutoff(text):

    return find_first(
        text,
        [
            r"VGM\s*CUT\s*OFF[^\n:]*[:]\s*([^\n\r]+)"
        ]
    )


def extract_si_cutoff(text):

    return find_first(
        text,
        [
            r"SI[_\s]*CUT[_\s]*OFF\s*DATE\s*[:]\s*([^\n\r]+)",
            r"SI\s*CUT\s*OFF[^\n:]*[:]\s*([^\n\r]+)"
        ]
    )


# =========================================================
# DATES
# =========================================================

def extract_etd(text):

    return find_first(
        text,
        [
            r"ETD\s*DATE\s*[,:>\-]*\s*(\d{4}/\d{2}/\d{2})"
        ]
    )


def extract_eta_dates(text):
    """
    Có thể có nhiều ETA trong document.

    Evergreen ví dụ:
    ETA POL: 2026/08/22
    ETA Destination: 2026/08/28
    """

    matches = re.findall(
        r"ETA\s*DATE[^\d]{0,10}"
        r"(\d{4}/\d{2}/\d{2})",
        text,
        re.IGNORECASE
    )

    # bỏ duplicate nhưng giữ thứ tự
    dates = []

    for date in matches:

        if date not in dates:
            dates.append(date)

    return dates


# =========================================================
# SHIPPER / CARGO
# =========================================================

def extract_shipper(text):

    return find_first(
        text,
        [
            r"SHIPPER\s*[:'’]?\s*([^\n\r]+)"
        ]
    )


def extract_commodity(text):

    return find_first(
        text,
        [
            r"COMMODITY\s*[:]\s*([^\n\r]+)"
        ]
    )


def extract_proper_shipping_name(text):

    return find_first(
        text,
        [
            r"PROPER\s+SHIPPING\s+NAME\s*[:\-]?\s*([^\n\r]+)"
        ]
    )


# =========================================================
# IMO / UN
# =========================================================

def extract_imo_details(text):

    # Trường hợp OCR đọc được:
    # 9/3082/ //Y

    match = re.search(
        r"\b([1-9])\s*/\s*(\d{4})\b",
        text
    )

    if match:

        return {
            "imo_class":
                match.group(1),

            "un_no":
                match.group(2),

            "raw":
                f"{match.group(1)} / {match.group(2)}"
        }

    return {
        "imo_class": "",
        "un_no": "",
        "raw": ""
    }


# =========================================================
# INLAND RETURN
# =========================================================

def extract_inland_return(text):

    return find_first(
        text,
        [
            r"INLAND\s+RETURN\s+TO\s*:\s*([^\n\r]+)"
        ]
    )


# =========================================================
# EMPTY PICKUP
# =========================================================

def extract_empty_pickup(text):

    return find_first(
        text,
        [
            r"EMPTY\s+PICK\s+UP\s+AT\s*:\s*([^\n\r]+)"
        ]
    )


# =========================================================
# PAYMENT TERM
# =========================================================

def extract_payment_term(text):

    return find_first(
        text,
        [
            r"PAYMENT\s+TERM\s*:\s*([A-Z ]+?)(?:\s+PARTIAL|\n|$)"
        ]
    )


# =========================================================
# MAIN UNIVERSAL EXTRACTOR
# =========================================================

def extract_booking_fields(text):

    carrier = detect_carrier(
        text
    )

    eta_dates = extract_eta_dates(
        text
    )

    imo = extract_imo_details(
        text
    )


    data = {

        "carrier_name":
            carrier,

        "booking_no":
            extract_booking_no(
                text
            ),

        "vessel_voyage":
            extract_vessel_voyage(
                text
            ),

        "port_of_receipt":
            extract_port_of_receipt(
                text
            ),

        "port_of_loading":
            extract_port_of_loading(
                text
            ),

        "port_of_discharge":
            extract_port_of_discharge(
                text
            ),

        "cy_cut_off":
            extract_cy_cutoff(
                text
            ),

        "vgm_cut_off":
            extract_vgm_cutoff(
                text
            ),

        "si_cut_off":
            extract_si_cutoff(
                text
            ),

        "pol_eta_date":
            (
                eta_dates[0]
                if len(eta_dates) >= 1
                else ""
            ),

        "etd_date":
            extract_etd(
                text
            ),

        "pod_eta_date":
            (
                eta_dates[-1]
                if len(eta_dates) >= 2
                else ""
            ),

        "shipper":
            extract_shipper(
                text
            ),

        "commodity":
            extract_commodity(
                text
            ),

        "proper_shipping_name":
            extract_proper_shipping_name(
                text
            ),

        "imo_class":
            imo["imo_class"],

        "un_no":
            imo["un_no"],

        "imo_details":
            imo["raw"],

        "empty_pickup":
            extract_empty_pickup(
                text
            ),

        "inland_return":
            extract_inland_return(
                text
            ),

        "payment_term":
            extract_payment_term(
                text
            )
    }

    return data