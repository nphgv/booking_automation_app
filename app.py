import streamlit as st
import pandas as pd
import os
import sys
import subprocess
from pdf_parser import read_pdf_bytes
from booking_extractor import extract_booking_fields
from bill_generator import generate_bill

from carrier_portal import (
    get_carrier_url,
    normalize_carrier,
)

from excel_database import (
    init_db,
    insert_booking,
    get_all_bookings,
    delete_booking,
    update_booking
)

from email_parser import parse_email


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Booking Automation Hub",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# DATABASE INIT
# =========================================================

init_db()


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .main-title {
        font-size: 34px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .subtitle {
        color: #777;
        font-size: 15px;
        margin-bottom: 25px;
    }

    .status-new {
        padding: 5px 10px;
        border-radius: 8px;
        background-color: #FFF3CD;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🚢 Booking Automation Hub</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="subtitle">
    Email → Booking → Carrier → Confirmation → Bill
    </div>
    """,
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Menu",
    [
        "Dashboard",
        "New Booking",
        "Booking Database",
        "PDF Confirmation",
        "Generate Bill",
        "Carrier Portal"
    ],
    label_visibility="collapsed"
)


# =========================================================
# DASHBOARD
# =========================================================

if page == "Dashboard":

    st.header("Dashboard")

    bookings = get_all_bookings()

    total = len(bookings)

    new_count = len(
        [
            x
            for x in bookings
            if x["status"] == "NEW"
        ]
    )

    confirmed_count = len(
        [
            x
            for x in bookings
            if x["status"] == "CONFIRMED"
        ]
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Bookings",
        total
    )

    col2.metric(
        "Waiting",
        new_count
    )

    col3.metric(
        "Confirmed",
        confirmed_count
    )

    st.divider()

    st.subheader("Recent Bookings")

    if not bookings:

        st.info(
            "Chưa có booking nào."
        )

    else:

        df = pd.DataFrame(
            bookings[:10]
        )

        columns = [
            "id",
            "customer_name",
            "carrier_name",
            "product_name",
            "cargo_weight",
            "booking_no",
            "status",
            "created_at"
        ]

        existing_columns = [
            col
            for col in columns
            if col in df.columns
        ]

        st.dataframe(
            df[existing_columns],
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# NEW BOOKING
# =========================================================

elif page == "New Booking":

    st.header("📩 New Booking")

    st.write(
        """
        Paste nội dung email của khách hàng.
        Hệ thống sẽ tự động phân tích các thông tin booking.
        """
    )

    email_text = st.text_area(
        "Email Content",
        height=300,
        placeholder="""
Ví dụ:

Dear Team,

Please book with MAERSK.

Commodity: Chemical Product ABC
HS Code: 382499
Cargo Weight: 24,500 KG
Volume: 52.5 CBM

Please use company account.
        """
    )

    analyze = st.button(
        "✨ Analyze Email",
        type="primary",
        use_container_width=True
    )

    if analyze:

        if not email_text.strip():

            st.warning(
                "Bạn chưa nhập nội dung email."
            )

        else:

            parsed = parse_email(
                email_text
            )

            st.session_state[
                "parsed_booking"
            ] = parsed

            st.success(
                "Đã phân tích email."
            )

       

    # =====================================================
    # REVIEW
    # =====================================================

    if "parsed_booking" in st.session_state:

        data = st.session_state[
            "parsed_booking"
        ]

        st.divider()

        st.subheader(
            "🔎 Review Booking Information"
        )

        st.caption(
            """
            Kiểm tra lại thông tin trước khi lưu.
            Bạn có thể sửa trực tiếp các ô bên dưới.
            """
        )

        # -------------------------------------------------
        # CUSTOMER
        # -------------------------------------------------

        st.markdown("#### Customer")

        col1, col2 = st.columns(2)

        with col1:

            customer_name = st.text_input(
                "Customer Name",
                value=data.get(
                    "customer_name",
                    ""
                )
            )

        with col2:

            customer_email = st.text_input(
                "Customer Email",
                value=data.get(
                    "customer_email",
                    ""
                )
            )

        # -------------------------------------------------
        # CARRIER
        # -------------------------------------------------

        st.markdown("#### Booking")

        col1, col2 = st.columns(2)

        carrier_options = [
            "",
            "MAERSK",
            "CMA CGM",
            "ONE",
            "MSC",
            "COSCO",
            "EVERGREEN",
            "OOCL",
            "HAPAG-LLOYD",
            "YANG MING"
        ]

        detected_carrier = data.get(
            "carrier_name",
            ""
        )

        try:

            carrier_index = (
                carrier_options.index(
                    detected_carrier
                )
            )

        except ValueError:

            carrier_index = 0

        with col1:

            carrier_name = st.selectbox(
                "Carrier",
                carrier_options,
                index=carrier_index
            )

        account_options = [
            "",
            "CUSTOMER",
            "COMPANY"
        ]

        detected_account = data.get(
            "booking_account",
            ""
        )

        try:

            account_index = (
                account_options.index(
                    detected_account
                )
            )

        except ValueError:

            account_index = 0

        with col2:

            booking_account = st.selectbox(
                "Booking Account",
                account_options,
                index=account_index
            )

        # -------------------------------------------------
        # CARGO
        # -------------------------------------------------

        st.markdown("#### Cargo")

        col1, col2 = st.columns(2)

        with col1:

            product_name = st.text_input(
                "Product / Commodity",
                value=data.get(
                    "product_name",
                    ""
                )
            )

        with col2:

            hs_code = st.text_input(
                "HS Code",
                value=data.get(
                    "hs_code",
                    ""
                )
            )

        col1, col2 = st.columns(2)

        with col1:

            cargo_weight = st.number_input(
                "Cargo Weight (KG)",
                min_value=0.0,
                value=float(
                    data.get(
                        "cargo_weight"
                    ) or 0
                ),
                step=1.0
            )

        with col2:

            cargo_volume = st.number_input(
                "Volume (CBM)",
                min_value=0.0,
                value=float(
                    data.get(
                        "cargo_volume"
                    ) or 0
                ),
                step=0.1
            )

        product_description = st.text_area(
            "Cargo / Email Description",
            value=data.get(
                "product_description",
                ""
            ),
            height=180
        )
        st.markdown("#### Route")

        col1, col2, col3 = st.columns(3)

        with col1:
            port_of_receipt = st.text_input(
                "Port of Receipt",
                value=data.get(
                    "port_of_receipt",
                    ""
                )
            )

        with col2:
            port_of_loading = st.text_input(
                "Port of Loading (POL)",
                value=data.get(
                    "port_of_loading",
                    ""
                )
            )

        with col3:
            port_of_discharge = st.text_input(
                "Port of Discharge (POD)",
                value=data.get(
                    "port_of_discharge",
                    ""
                )
            )

        st.markdown("#### Container / Schedule")

        col1, col2 = st.columns(2)

        with col1:
            container_quantity = st.text_input(
                "Container Quantity",
                value=data.get(
                    "container_quantity",
                    ""
                )
            )

        with col2:
            etd_date = st.text_input(
                "ETD",
                value=data.get(
                    "etd_date",
                    ""
                )
            )

        st.markdown("#### Dangerous Goods")

        col1, col2 = st.columns(2)

        with col1:
            imo_class = st.text_input(
                "IMO Class",
                value=data.get(
                    "imo_class",
                    ""
                )
            )

        with col2:
            un_no = st.text_input(
                "UN No.",
                value=data.get(
                    "un_no",
                    ""
                )
            )

        proper_shipping_name = st.text_area(
            "Proper Shipping Name",
            value=data.get(
                "proper_shipping_name",
                ""
            ),
            height=100
        )        

        # -------------------------------------------------
        # BILL INFORMATION
        # -------------------------------------------------

        st.markdown("#### Bill Information")

        shipper = st.text_area(
            "Shipper",
            height=100
        )

        consignee = st.text_area(
            "Consignee",
            height=100
        )

        notify_party = st.text_area(
            "Notify Party",
            height=100
        )

        col1, col2 = st.columns(2)

        with col1:

            package_quantity = st.text_input(
                "Package Quantity"
            )

        with col2:

            package_type = st.text_input(
                "Package Type"
            )

        marks_numbers = st.text_area(
            "Marks & Numbers",
            height=100
        )

        st.divider()

        # -------------------------------------------------
        # SAVE
        # -------------------------------------------------

        if st.button(
            "💾 Save Booking",
            type="primary",
            use_container_width=True
        ):

            booking_data = {

                "customer_name":
                    customer_name,

                "customer_email":
                    customer_email,

                "carrier_name":
                    carrier_name,

                "booking_account":
                    booking_account,

                "product_name":
                    product_name,

                "product_description":
                    product_description,

                "hs_code":
                    hs_code,

                "cargo_weight":
                    cargo_weight,

                "cargo_volume":
                    cargo_volume,
                "port_of_receipt":
                    port_of_receipt,

                "port_of_loading":
                    port_of_loading,

                "port_of_discharge":
                    port_of_discharge,

                "container_quantity":
                    container_quantity,

                "etd_date":
                    etd_date,

                "imo_details":
                    (
                        f"IMO {imo_class} / UN {un_no}"
                        if imo_class or un_no
                        else ""
                    ),
                "shipper":
                    shipper,

                "consignee":
                    consignee,

                "notify_party":
                    notify_party,

                "package_quantity":
                    package_quantity,

                "package_type":
                    package_type,

                "marks_numbers":
                    marks_numbers,

                "status":
                    "NEW"
            }

            booking_id = insert_booking(
                booking_data
            )

            st.success(
                f"✅ Booking #{booking_id} đã được lưu."
            )

            del st.session_state[
                "parsed_booking"
            ]

            st.rerun()


# =========================================================
# BOOKING DATABASE
# =========================================================

elif page == "Booking Database":

    st.header("🗃 Booking Database")

    bookings = get_all_bookings()

    if not bookings:

        st.info(
            "Database chưa có booking."
        )

    else:

        df = pd.DataFrame(
            bookings
        )

        # Search
        search = st.text_input(
            "🔎 Search",
            placeholder=(
                "Carrier, customer, booking no..."
            )
        )

        if search:

            mask = df.astype(
                str
            ).apply(
                lambda row:
                    row.str.contains(
                        search,
                        case=False,
                        na=False
                    ).any(),
                axis=1
            )

            df = df[mask]

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader(
            "Delete Booking"
        )

        booking_ids = [
            booking["id"]
            for booking in bookings
        ]

        delete_id = st.selectbox(
            "Booking ID",
            booking_ids
        )

        confirm_delete = st.checkbox(
            "Tôi xác nhận muốn xóa booking này"
        )

        if st.button(
            "🗑 Delete",
            disabled=not confirm_delete
        ):

            success = delete_booking(
                delete_id
            )

            if success:

                st.success(
                    f"Đã xóa Booking #{delete_id}"
                )

                st.rerun()


# =========================================================
# PDF CONFIRMATION
# =========================================================

elif page == "PDF Confirmation":

    st.header(
        "📄 Booking Confirmation"
    )

    st.caption(
        """
        Chọn booking và upload file confirmation
        từ hãng tàu.

        Hệ thống tự nhận biết PDF text hoặc
        PDF scan.
        """
    )


    # =====================================================
    # GET BOOKINGS
    # =====================================================

    bookings = get_all_bookings()


    if not bookings:

        st.warning(
            """
            Chưa có booking trong database.

            Hãy tạo booking trước.
            """
        )

        st.stop()


    # =====================================================
    # SELECT BOOKING
    # =====================================================

    st.subheader(
        "1. Select Booking"
    )


    booking_options = {}

    for booking in bookings:

        booking_id = (
            booking["id"]
        )

        carrier = (
            booking.get(
                "carrier_name"
            )
            or "NO CARRIER"
        )

        customer = (
            booking.get(
                "customer_name"
            )
            or "NO CUSTOMER"
        )

        product = (
            booking.get(
                "product_name"
            )
            or "NO PRODUCT"
        )

        label = (
            f"#{booking_id} | "
            f"{carrier} | "
            f"{customer} | "
            f"{product}"
        )

        booking_options[
            label
        ] = booking_id


    selected_label = (
        st.selectbox(
            "Booking",
            list(
                booking_options.keys()
            )
        )
    )


    selected_booking_id = (
        booking_options[
            selected_label
        ]
    )


    # =====================================================
    # UPLOAD PDF
    # =====================================================

    st.divider()

    st.subheader(
        "2. Upload Confirmation"
    )


    pdf_file = st.file_uploader(
        "Booking Confirmation PDF",
        type=[
            "pdf"
        ],
        key="confirmation_pdf"
    )


    # =====================================================
    # READ PDF
    # =====================================================

    if pdf_file is not None:

        st.write(
            f"**File:** {pdf_file.name}"
        )

        st.write(
            f"**Size:** "
            f"{pdf_file.size / 1024:.1f} KB"
        )


        if st.button(
            "🔍 Read PDF",
            type="primary",
            use_container_width=True
        ):

            pdf_bytes = (
                pdf_file.getvalue()
            )


            with st.spinner(
                """
                Đang đọc PDF...

                File scan có thể mất
                một chút thời gian vì cần OCR.
                """
            ):

                try:

                    result = (
                        read_pdf_bytes(
                            pdf_bytes,
                            pdf_file.name
                        )
                    )

                    st.session_state[
                        "pdf_result"
                    ] = result

                    extracted_data = extract_booking_fields(
                        result["full_text"]
                    )

                    st.session_state[
                        "extracted_booking"
                    ] = extracted_data

                    st.session_state[
                        "pdf_booking_id"
                    ] = (
                        selected_booking_id
                    )


                except Exception as error:

                    st.error(
                        "Không thể đọc PDF."
                    )

                    st.exception(
                        error
                    )


    # =====================================================
    # SHOW RESULT
    # =====================================================

    if (
        "pdf_result"
        in st.session_state
    ):

        result = (
            st.session_state[
                "pdf_result"
            ]
        )

        st.divider()

        st.subheader(
            "3. PDF Reader Result"
        )


        col1, col2, col3, col4 = (
            st.columns(4)
        )


        col1.metric(
            "Document Type",
            result[
                "document_type"
            ]
        )


        col2.metric(
            "Pages",
            result[
                "total_pages"
            ]
        )


        col3.metric(
            "Native",
            result[
                "native_pages"
            ]
        )


        col4.metric(
            "OCR",
            result[
                "ocr_pages"
            ]
        )


        # =================================================
        # PAGE STATUS
        # =================================================

        st.markdown(
            "#### Page Processing"
        )


        page_table = []

        for page_data in (
            result["pages"]
        ):

            page_table.append(
                {
                    "Page":
                        page_data[
                            "page_number"
                        ],

                    "Method":
                        page_data[
                            "method"
                        ],

                    "Characters":
                        page_data[
                            "character_count"
                        ]
                }
            )


        page_df = (
            pd.DataFrame(
                page_table
            )
        )


        st.dataframe(
            page_df,
            use_container_width=True,
            hide_index=True
        )


        # =================================================
        # RAW TEXT
        # =================================================

        st.markdown(
            "#### Extracted Text"
        )


        st.text_area(
            "Raw document text",
            value=result[
                "full_text"
            ],
            height=500
        )


        st.info(
            """
            Đây là raw text mà hệ thống đọc được.

            Bước tiếp theo sẽ tự động biến
            text này thành Booking No.,
            Vessel/Voyage, POL, POD,
            Cut-off, ETD, ETA...
            """
        )


# =========================================================
# GENERATE BILL
# =========================================================

    # =====================================================
    # EXTRACTED BOOKING DATA
    # =====================================================

    if (
        "extracted_booking"
        in st.session_state
    ):

        extracted = st.session_state[
            "extracted_booking"
        ]

        st.divider()

        st.subheader(
            "4. Review Booking Information"
        )

        st.caption(
            """
            Hệ thống đã tự đọc dữ liệu từ PDF.
            Bạn kiểm tra và sửa nếu OCR đọc sai.
            """
        )

        col1, col2 = st.columns(2)

        with col1:

            carrier_name = st.text_input(
                "Carrier",
                value=extracted.get(
                    "carrier_name",
                    ""
                )
            )

            booking_no = st.text_input(
                "Booking No.",
                value=extracted.get(
                    "booking_no",
                    ""
                )
            )

            vessel_voyage = st.text_input(
                "Vessel / Voyage",
                value=extracted.get(
                    "vessel_voyage",
                    ""
                )
            )

            port_of_receipt = st.text_input(
                "Port of Receipt",
                value=extracted.get(
                    "port_of_receipt",
                    ""
                )
            )

            port_of_loading = st.text_input(
                "Port of Loading",
                value=extracted.get(
                    "port_of_loading",
                    ""
                )
            )

        with col2:

            port_of_discharge = st.text_input(
                "Port of Discharge",
                value=extracted.get(
                    "port_of_discharge",
                    ""
                )
            )

            cy_cut_off = st.text_input(
                "CY Cut-off",
                value=extracted.get(
                    "cy_cut_off",
                    ""
                )
            )

            vgm_cut_off = st.text_input(
                "VGM Cut-off",
                value=extracted.get(
                    "vgm_cut_off",
                    ""
                )
            )

            si_cut_off = st.text_input(
                "SI Cut-off",
                value=extracted.get(
                    "si_cut_off",
                    ""
                )
            )

            etd_date = st.text_input(
                "ETD",
                value=extracted.get(
                    "etd_date",
                    ""
                )
            )

        st.markdown("#### Schedule")

        col1, col2 = st.columns(2)

        with col1:

            pol_eta_date = st.text_input(
                "POL ETA",
                value=extracted.get(
                    "pol_eta_date",
                    ""
                )
            )

        with col2:

            pod_eta_date = st.text_input(
                "Destination ETA",
                value=extracted.get(
                    "pod_eta_date",
                    ""
                )
            )

        st.markdown("#### Cargo")

        commodity = st.text_input(
            "Commodity",
            value=extracted.get(
                "commodity",
                ""
            )
        )

        proper_shipping_name = st.text_area(
            "Proper Shipping Name",
            value=extracted.get(
                "proper_shipping_name",
                ""
            ),
            height=100
        )

        col1, col2 = st.columns(2)

        with col1:

            imo_class = st.text_input(
                "IMO Class",
                value=extracted.get(
                    "imo_class",
                    ""
                )
            )

        with col2:

            un_no = st.text_input(
                "UN No.",
                value=extracted.get(
                    "un_no",
                    ""
                )
            )

        empty_pickup = st.text_area(
            "Empty Pick Up",
            value=extracted.get(
                "empty_pickup",
                ""
            ),
            height=80
        )

        inland_return = st.text_area(
            "Inland Return",
            value=extracted.get(
                "inland_return",
                ""
            ),
            height=80
        )
        st.divider()

        if st.button(
            "✅ Confirm & Save to Database",
            type="primary",
            width="stretch",
            key="confirm_save_booking_pdf"
        ):

            booking_id = st.session_state.get(
                "pdf_booking_id"
            )

            if booking_id is None:

                st.error(
                    "Không xác định được Booking ID."
                )

            else:

                update_data = {
                    "carrier_name": carrier_name,
                    "booking_no": booking_no,
                    "vessel_voyage": vessel_voyage,
                    "port_of_receipt": port_of_receipt,
                    "port_of_loading": port_of_loading,
                    "port_of_discharge": port_of_discharge,
                    "cy_cut_off": cy_cut_off,
                    "vgm_cut_off": vgm_cut_off,
                    "si_cut_off": si_cut_off,
                    "etd_date": etd_date,
                    "eta_date": pod_eta_date,

                    "imo_details": (
                        f"IMO {imo_class} / UN {un_no}"
                        if imo_class or un_no
                        else ""
                    ),

                    "inland_return": inland_return,
                    "product_name": commodity,

                    "source_pdf": st.session_state[
                        "pdf_result"
                    ]["file_name"],

                    "status": "CONFIRMED"
                }

                success = update_booking(
                    booking_id,
                    update_data
                )

                if success:

                    st.success(
                        f"✅ Booking #{booking_id} đã được cập nhật vào database."
                    )

                else:

                    st.error(
                        "Không cập nhật được booking."
                    )        

elif page == "Generate Bill":

    st.header(
        "🧾 Generate Bill"
    )

    st.caption(
        """
        Chọn booking trong Excel database
        và tạo Bill từ FORM_BILL.xlsx.
        """
    )


    # =====================================================
    # LOAD BOOKINGS
    # =====================================================

    bookings = get_all_bookings()

    if not bookings:

        st.warning(
            "Chưa có booking trong database."
        )

        st.stop()


    # =====================================================
    # SELECT BOOKING
    # =====================================================

    booking_options = {}

    for booking in bookings:

        booking_id = (
            booking.get("id")
            or ""
        )

        customer = (
            booking.get(
                "customer_name"
            )
            or "NO CUSTOMER"
        )

        carrier = (
            booking.get(
                "carrier_name"
            )
            or "NO CARRIER"
        )

        booking_no = (
            booking.get(
                "booking_no"
            )
            or "NO BOOKING NO."
        )

        label = (
            f"{booking_id} | "
            f"{carrier} | "
            f"{customer} | "
            f"{booking_no}"
        )

        booking_options[
            label
        ] = booking


    selected_label = st.selectbox(
        "Select Booking",
        list(
            booking_options.keys()
        ),
        key="bill_booking_select"
    )


    selected_booking = (
        booking_options[
            selected_label
        ]
    )


    # =====================================================
    # PREVIEW DATA
    # =====================================================

    st.divider()

    st.subheader(
        "Booking Information"
    )

    col1, col2 = st.columns(2)


    with col1:

        st.write(
            "**Booking ID:**",
            selected_booking.get(
                "id",
                ""
            )
        )

        st.write(
            "**Carrier:**",
            selected_booking.get(
                "carrier_name",
                ""
            )
        )

        st.write(
            "**Booking No:**",
            selected_booking.get(
                "booking_no",
                ""
            )
        )

        st.write(
            "**Vessel/Voyage:**",
            selected_booking.get(
                "vessel_voyage",
                ""
            )
        )


    with col2:

        st.write(
            "**POL:**",
            selected_booking.get(
                "port_of_loading",
                ""
            )
        )

        st.write(
            "**POD:**",
            selected_booking.get(
                "port_of_discharge",
                ""
            )
        )

        st.write(
            "**Container:**",
            selected_booking.get(
                "container_quantity",
                ""
            )
        )

        st.write(
            "**Weight:**",
            selected_booking.get(
                "cargo_weight",
                ""
            )
        )


    # =====================================================
    # GENERATE
    # =====================================================

    st.divider()


    if st.button(
        "🧾 Generate Bill Excel",
        type="primary",
        width="stretch",
        key="generate_bill_excel"
    ):

        try:

            with st.spinner(
                "Đang tạo Bill..."
            ):

                output_file = (
                    generate_bill(
                        selected_booking
                    )
                )


                # Update Bill File trong Excel database
                update_booking(
                    selected_booking[
                        "id"
                    ],
                    {
                        "bill_file":
                            output_file
                    }
                )


                st.session_state[
                    "generated_bill_file"
                ] = output_file


            st.success(
                "✅ Bill đã được tạo."
            )


        except Exception as error:

            st.error(
                "Không thể tạo Bill."
            )

            st.exception(
                error
            )


    # =====================================================
    # DOWNLOAD
    # =====================================================

    generated_file = (
        st.session_state.get(
            "generated_bill_file"
        )
    )


    if (
        generated_file
        and
        os.path.exists(
            generated_file
        )
    ):

        with open(
            generated_file,
            "rb"
        ) as file:

            file_bytes = (
                file.read()
            )


        st.download_button(
            label="⬇️ Download Bill",
            data=file_bytes,
            file_name=os.path.basename(
                generated_file
            ),
            mime=(
                "application/"
                "vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            width="stretch",
            key="download_generated_bill"
        )
# =========================================================
# CARRIER PORTAL
# =========================================================

elif page == "Carrier Portal":

    st.header("🌐 Carrier Portal")

    st.caption(
        """
        Chọn booking trong Excel database.
        App sẽ kiểm tra dữ liệu và mở đúng portal hãng tàu.
        """
    )

    bookings = get_all_bookings()

    if not bookings:

        st.warning(
            "Chưa có booking trong Excel database."
        )

        st.stop()


    # =====================================================
    # SELECT BOOKING
    # =====================================================

    booking_options = {}

    for booking in bookings:

        booking_id = (
            booking.get("id")
            or ""
        )

        carrier = (
            booking.get("carrier_name")
            or "NO CARRIER"
        )

        customer = (
            booking.get("customer_name")
            or "NO CUSTOMER"
        )

        product = (
            booking.get("product_name")
            or "NO PRODUCT"
        )

        label = (
            f"{booking_id} | "
            f"{carrier} | "
            f"{customer} | "
            f"{product}"
        )

        booking_options[
            label
        ] = booking


    selected_label = st.selectbox(
        "Select Booking",
        list(
            booking_options.keys()
        ),
        key="carrier_booking_select"
    )


    booking = (
        booking_options[
            selected_label
        ]
    )


    # =====================================================
    # BOOKING INFO
    # =====================================================

    st.divider()

    st.subheader(
        "Booking Information"
    )


    col1, col2 = st.columns(2)


    with col1:

        st.write(
            "**Booking ID:**",
            booking.get(
                "id",
                ""
            )
        )

        st.write(
            "**Carrier:**",
            booking.get(
                "carrier_name",
                ""
            )
        )

        st.write(
            "**Product:**",
            booking.get(
                "product_name",
                ""
            )
        )

        st.write(
            "**HS Code:**",
            booking.get(
                "hs_code",
                ""
            )
        )

        st.write(
            "**Weight:**",
            booking.get(
                "cargo_weight",
                ""
            )
        )


    with col2:

        st.write(
            "**Container:**",
            booking.get(
                "container_quantity",
                ""
            )
        )

        st.write(
            "**Port of Receipt:**",
            booking.get(
                "port_of_receipt",
                ""
            )
        )

        st.write(
            "**POL:**",
            booking.get(
                "port_of_loading",
                ""
            )
        )

        st.write(
            "**POD:**",
            booking.get(
                "port_of_discharge",
                ""
            )
        )

        st.write(
            "**Booking Account:**",
            booking.get(
                "booking_account",
                ""
            )
        )


    # =====================================================
    # CHECK REQUIRED DATA
    # =====================================================

    required_fields = {
        "Carrier": booking.get(
            "carrier_name"
        ),

        "Booking Account": booking.get(
            "booking_account"
        ),

        "Customer": booking.get(
            "customer_name"
        ),

        "Product / Commodity": booking.get(
            "product_name"
        ),

        "HS Code": booking.get(
            "hs_code"
        ),

        "Cargo Weight": booking.get(
            "cargo_weight"
        ),

        "Container": booking.get(
            "container_quantity"
        ),

        "Port of Receipt": booking.get(
            "port_of_receipt"
        ),

        "POL": booking.get(
            "port_of_loading"
        ),

        "POD": booking.get(
            "port_of_discharge"
        ),

        "Shipper": booking.get(
            "shipper"
        ),

        "Consignee": booking.get(
            "consignee"
        ),
    }


    missing_fields = [
        field
        for field, value
        in required_fields.items()
        if value is None
        or str(value).strip() == ""
    ]


    st.divider()

    st.subheader(
        "Portal Check"
    )


    if missing_fields:

        st.warning(
            "Thiếu dữ liệu: "
            + ", ".join(
                missing_fields
            )
        )

    else:

        st.success(
            "Dữ liệu cơ bản đã đủ để mở portal."
        )

    # =====================================================
    # BOOKING DATA PREPARATION
    # =====================================================

    st.markdown(
        "#### Booking Data Preparation"
    )


    dg_value = booking.get(
        "imo_details"
    )

    is_dangerous_goods = bool(
        dg_value
        and str(dg_value).strip()
    )


    portal_data = {
        "Booking ID":
            booking.get("id", ""),

        "Booking Account":
            booking.get(
                "booking_account",
                ""
            ),

        "Customer":
            booking.get(
                "customer_name",
                ""
            ),

        "Shipper":
            booking.get(
                "shipper",
                ""
            ),

        "Consignee":
            booking.get(
                "consignee",
                ""
            ),

        "Port of Receipt":
            booking.get(
                "port_of_receipt",
                ""
            ),

        "Port of Loading":
            booking.get(
                "port_of_loading",
                ""
            ),

        "Port of Discharge":
            booking.get(
                "port_of_discharge",
                ""
            ),

        "Container":
            booking.get(
                "container_quantity",
                ""
            ),

        "Commodity":
            booking.get(
                "product_name",
                ""
            ),

        "HS Code":
            booking.get(
                "hs_code",
                ""
            ),

        "Gross Weight":
            booking.get(
                "cargo_weight",
                ""
            ),

        "Volume":
            booking.get(
                "cargo_volume",
                ""
            ),

        "Dangerous Goods":
            "YES"
            if is_dangerous_goods
            else "NO",

        "IMO / UN":
            dg_value or "",
    }


    portal_df = pd.DataFrame(
        [
            {
                "Field": field,
                "Value": value
            }
            for field, value
            in portal_data.items()
        ]
    )


    st.dataframe(
        portal_df,
        width="stretch",
        hide_index=True
    )


    if missing_fields:

        st.error(
            "BOOKING DATA: NOT READY"
        )

    else:

        st.success(
            "BOOKING DATA: READY"
        )
    # =====================================================
    # CARRIER
    # =====================================================

    carrier = normalize_carrier(
        booking.get(
            "carrier_name"
        )
    )


    portal_url = get_carrier_url(
        carrier
    )


    if portal_url:

        st.write(
            "**Portal:**",
            portal_url
        )

    else:

        st.error(
            f"Chưa cấu hình portal cho hãng {carrier}."
        )


    # =====================================================
    # OPEN PORTAL
    # =====================================================

    if portal_url:

        st.link_button(
            f"🌐 Open {carrier} Portal",
            portal_url,
            width="stretch"
        )
        if st.button(
            f"🤖 Open {carrier} with Playwright",
            type="primary",
            width="stretch",
            key="open_carrier_playwright"
        ):

            try:

                subprocess.Popen(
                    [
                        sys.executable,
                        "carrier_portal.py",
                        carrier
                    ],
                    cwd=os.getcwd()
                )

                st.success(
                    f"Đang mở {carrier} Login bằng Playwright..."
                )

            except Exception as error:

                st.error(
                    "Không mở được Playwright browser."
                )

                st.exception(
                    error
                )

