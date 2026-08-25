import os
import sqlite3
from dotenv import load_dotenv


# ==========================================
# LOAD ENVIRONMENT
# ==========================================

load_dotenv()

DB_PATH = os.getenv(
    "DATABASE_PATH",
    "data/bookings.db"
)


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_connection():
    """
    Tạo kết nối đến SQLite database.
    """

    db_folder = os.path.dirname(DB_PATH)

    if db_folder:
        os.makedirs(
            db_folder,
            exist_ok=True
        )

    conn = sqlite3.connect(DB_PATH)

    # Cho phép lấy dữ liệu theo tên column
    conn.row_factory = sqlite3.Row

    return conn


# ==========================================
# INITIALIZE DATABASE
# ==========================================

def init_db():
    """
    Tạo bảng bookings nếu chưa tồn tại.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- Thông tin khách hàng
            customer_name TEXT,
            customer_email TEXT,

            -- Thông tin booking ban đầu
            carrier_name TEXT,
            booking_account TEXT,

            -- Thông tin hàng hóa
            product_name TEXT,
            product_description TEXT,
            hs_code TEXT,

            cargo_weight REAL,
            cargo_volume REAL,

            -- Thông tin sau khi hãng tàu confirm
            booking_no TEXT,
            vessel_voyage TEXT,

            port_of_receipt TEXT,
            port_of_loading TEXT,
            port_of_discharge TEXT,

            cy_cut_off TEXT,
            vgm_cut_off TEXT,
            si_cut_off TEXT,

            etd_date TEXT,
            eta_date TEXT,

            container_quantity TEXT,

            gwt_plus_tare TEXT,
            limit_gwt_each TEXT,

            imo_details TEXT,
            inland_return TEXT,

            -- Bill information
            shipper TEXT,
            consignee TEXT,
            notify_party TEXT,

            marks_numbers TEXT,
            package_quantity TEXT,
            package_type TEXT,

            -- File PDF confirmation
            source_pdf TEXT,

            -- Trạng thái xử lý
            status TEXT DEFAULT 'NEW',

            -- Ngày tạo
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            -- Ngày cập nhật
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()


# ==========================================
# INSERT BOOKING
# ==========================================

def insert_booking(data):
    """
    Tạo booking mới.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO bookings (

            customer_name,
            customer_email,

            carrier_name,
            booking_account,

            product_name,
            product_description,
            hs_code,

            cargo_weight,
            cargo_volume,

            port_of_receipt,
            port_of_loading,
            port_of_discharge,

            etd_date,

            container_quantity,

            imo_details,

            shipper,
            consignee,
            notify_party,

            marks_numbers,
            package_quantity,
            package_type,

            status
        )

        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """,
        (
            data.get("customer_name"),
            data.get("customer_email"),

            data.get("carrier_name"),
            data.get("booking_account"),

            data.get("product_name"),
            data.get("product_description"),
            data.get("hs_code"),

            data.get("cargo_weight"),
            data.get("cargo_volume"),

            data.get("port_of_receipt"),
            data.get("port_of_loading"),
            data.get("port_of_discharge"),

            data.get("etd_date"),

            data.get("container_quantity"),

            data.get("imo_details"),

            data.get("shipper"),
            data.get("consignee"),
            data.get("notify_party"),

            data.get("marks_numbers"),
            data.get("package_quantity"),
            data.get("package_type"),

            data.get("status", "NEW")
        )
    )

    booking_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return booking_id


# ==========================================
# GET ALL BOOKINGS
# ==========================================

def get_all_bookings():
    """
    Lấy toàn bộ booking.
    Booking mới nhất nằm trên cùng.
    """

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT *
        FROM bookings
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


# ==========================================
# GET ONE BOOKING
# ==========================================

def get_booking(booking_id):
    """
    Lấy một booking theo ID.
    """

    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM bookings
        WHERE id = ?
        """,
        (booking_id,)
    ).fetchone()

    conn.close()

    if row is None:
        return None

    return dict(row)


# ==========================================
# UPDATE BOOKING
# ==========================================

def update_booking(booking_id, data):
    """
    Update các field được truyền vào.

    Ví dụ:

    update_booking(
        1,
        {
            "booking_no": "ABC123",
            "vessel_voyage": "EVER GIVEN 001E"
        }
    )
    """

    if not data:
        return False

    # Các field được phép update
    allowed_fields = {

        "customer_name",
        "customer_email",

        "carrier_name",
        "booking_account",

        "product_name",
        "product_description",
        "hs_code",

        "cargo_weight",
        "cargo_volume",

        "booking_no",
        "vessel_voyage",

        "port_of_receipt",
        "port_of_loading",
        "port_of_discharge",

        "cy_cut_off",
        "vgm_cut_off",
        "si_cut_off",

        "etd_date",
        "eta_date",

        "container_quantity",

        "gwt_plus_tare",
        "limit_gwt_each",

        "imo_details",
        "inland_return",

        "shipper",
        "consignee",
        "notify_party",

        "marks_numbers",
        "package_quantity",
        "package_type",

        "source_pdf",

        "status"
    }

    clean_data = {
        key: value
        for key, value in data.items()
        if key in allowed_fields
    }

    if not clean_data:
        return False

    set_clause = ", ".join(
        f"{key} = ?"
        for key in clean_data
    )

    values = list(
        clean_data.values()
    )

    values.append(
        booking_id
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        f"""
        UPDATE bookings

        SET
            {set_clause},
            updated_at = CURRENT_TIMESTAMP

        WHERE id = ?
        """,
        values
    )

    conn.commit()

    success = cursor.rowcount > 0

    conn.close()

    return success


# ==========================================
# DELETE BOOKING
# ==========================================

def delete_booking(booking_id):
    """
    Xóa booking theo ID.
    """

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM bookings
        WHERE id = ?
        """,
        (booking_id,)
    )

    conn.commit()

    success = cursor.rowcount > 0

    conn.close()

    return success


# ==========================================
# RUN DIRECTLY
# ==========================================

if __name__ == "__main__":

    init_db()

    print(
        f"Database initialized successfully: {DB_PATH}"
    )