import os
import sys

from playwright.sync_api import sync_playwright


# =========================================================
# CARRIER URLS
# =========================================================

CARRIER_URLS = {
    "EVERGREEN": "https://www.shipmentlink.com/",
}


# =========================================================
# NORMALIZE CARRIER
# =========================================================

def normalize_carrier(carrier_name):

    carrier = str(
        carrier_name or ""
    ).upper().strip()

    if "EVERGREEN" in carrier:
        return "EVERGREEN"

    if "MAERSK" in carrier:
        return "MAERSK"

    if "CMA CGM" in carrier:
        return "CMA CGM"

    if carrier in [
        "ONE",
        "OCEAN NETWORK EXPRESS"
    ]:
        return "ONE"

    if "MSC" in carrier:
        return "MSC"

    if "COSCO" in carrier:
        return "COSCO"

    if "OOCL" in carrier:
        return "OOCL"

    if "HAPAG" in carrier:
        return "HAPAG-LLOYD"

    return carrier


# =========================================================
# GET URL
# =========================================================

def get_carrier_url(carrier_name):

    carrier = normalize_carrier(
        carrier_name
    )

    return CARRIER_URLS.get(
        carrier
    )


# =========================================================
# PLAYWRIGHT PROFILE
# =========================================================

def get_profile_path(carrier):

    base_folder = os.path.join(
        os.getcwd(),
        "browser_profiles"
    )

    os.makedirs(
        base_folder,
        exist_ok=True
    )

    carrier_folder = (
        carrier
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )

    return os.path.join(
        base_folder,
        carrier_folder
    )


# =========================================================
# OPEN PORTAL
# =========================================================

def open_carrier_browser(carrier_name):

    carrier = normalize_carrier(
        carrier_name
    )

    url = get_carrier_url(
        carrier
    )

    if not url:

        raise ValueError(
            f"Chưa cấu hình portal cho hãng: {carrier}"
        )

    profile_path = get_profile_path(
        carrier
    )

    print()
    print("=" * 60)
    print("CARRIER PORTAL")
    print("=" * 60)
    print("Carrier:", carrier)
    print("URL:", url)
    print("Profile:", profile_path)
    print()

    with sync_playwright() as p:

        context = (
            p.chromium.launch_persistent_context(
                user_data_dir=profile_path,

                headless=False,

                viewport={
                    "width": 1440,
                    "height": 900
                },

                args=[
                    "--start-maximized"
                ]
            )
        )

        if context.pages:

            page = context.pages[0]

        else:

            page = context.new_page()

        if carrier == "EVERGREEN":

            login_url = (
                "https://www.shipmentlink.com/"
                "tam1/jsp/TAM1_Login.jsp?lang=e"
            )

            page.goto(
                login_url,
                wait_until="domcontentloaded"
            )

            print(
                "Evergreen Login page opened."
            )

        else:

            page.goto(
                url,
                wait_until="domcontentloaded"
            )
        print(
            "Browser đã mở."
        )

        print(
            "Login thủ công nếu cần."
        )

        print(
            "Khi hoàn tất, đóng cửa sổ Chromium."
        )

        # Giữ process sống cho tới khi browser bị đóng
        try:

            page.wait_for_timeout(
                24 * 60 * 60 * 1000
            )

        except Exception:

            pass

        finally:

            try:
                context.close()
            except Exception:
                pass


# =========================================================
# CLI
# =========================================================

if __name__ == "__main__":

    carrier = "EVERGREEN"

    if len(sys.argv) >= 2:

        carrier = sys.argv[1]

    open_carrier_browser(
        carrier
    )