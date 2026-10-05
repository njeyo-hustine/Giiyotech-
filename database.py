import sqlite3
from datetime import date, timedelta
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).with_name("giiyo_operations.db")


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_date TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount >= 0),
                category TEXT NOT NULL,
                programme TEXT NOT NULL,
                paid_by TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                notes TEXT,
                receipt_available INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
                programme TEXT NOT NULL,
                location TEXT NOT NULL,
                responsible_person TEXT,
                condition TEXT NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def add_expense(expense_date, amount, category, programme, paid_by,
                payment_method, notes, receipt_available):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO expenses
            (expense_date, amount, category, programme, paid_by,
             payment_method, notes, receipt_available)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            expense_date, amount, category, programme, paid_by,
            payment_method, notes, int(receipt_available)
        ))


def get_expenses(month=None, programme=None):
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []

    if month:
        query += " AND substr(expense_date, 1, 7) = ?"
        params.append(month)

    if programme and programme != "All":
        query += " AND programme = ?"
        params.append(programme)

    query += " ORDER BY expense_date DESC, id DESC"

    with get_connection() as conn:
        return conn.execute(query, params).fetchall()


def get_expense_programmes():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT programme FROM expenses ORDER BY programme"
        ).fetchall()
        return [row["programme"] for row in rows]


def get_expense_total(month=None, programme=None):
    query = "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE 1=1"
    params = []

    if month:
        query += " AND substr(expense_date, 1, 7) = ?"
        params.append(month)

    if programme and programme != "All":
        query += " AND programme = ?"
        params.append(programme)

    with get_connection() as conn:
        return float(conn.execute(query, params).fetchone()["total"])


def get_spending_by_programme(month=None):
    query = """
        SELECT programme, COALESCE(SUM(amount), 0) AS total
        FROM expenses
        WHERE 1=1
    """
    params = []

    if month:
        query += " AND substr(expense_date, 1, 7) = ?"
        params.append(month)

    query += " GROUP BY programme ORDER BY total DESC"

    with get_connection() as conn:
        return conn.execute(query, params).fetchall()


def add_inventory(item_name, quantity, programme, location,
                  responsible_person, condition, notes):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO inventory
            (item_name, quantity, programme, location,
             responsible_person, condition, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            item_name, quantity, programme, location,
            responsible_person, condition, notes
        ))


def get_inventory():
    with get_connection() as conn:
        return conn.execute("""
            SELECT * FROM inventory
            ORDER BY
                CASE condition
                    WHEN 'Missing' THEN 1
                    WHEN 'Damaged' THEN 2
                    WHEN 'Low Quantity' THEN 3
                    ELSE 4
                END,
                item_name COLLATE NOCASE
        """).fetchall()


def get_inventory_item(item_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM inventory WHERE id = ?", (item_id,)
        ).fetchone()


def update_inventory(item_id, item_name, quantity, programme, location,
                     responsible_person, condition, notes):
    with get_connection() as conn:
        conn.execute("""
            UPDATE inventory
            SET item_name = ?,
                quantity = ?,
                programme = ?,
                location = ?,
                responsible_person = ?,
                condition = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            item_name, quantity, programme, location,
            responsible_person, condition, notes, item_id
        ))


def delete_inventory(item_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM inventory WHERE id = ?", (item_id,))


def get_inventory_count():
    with get_connection() as conn:
        return int(conn.execute(
            "SELECT COUNT(*) AS count FROM inventory"
        ).fetchone()["count"])


def get_attention_items():
    with get_connection() as conn:
        return conn.execute("""
            SELECT * FROM inventory
            WHERE condition IN ('Damaged', 'Missing', 'Low Quantity')
               OR quantity <= 0
            ORDER BY
                CASE condition
                    WHEN 'Missing' THEN 1
                    WHEN 'Damaged' THEN 2
                    WHEN 'Low Quantity' THEN 3
                    ELSE 4
                END,
                item_name COLLATE NOCASE
        """).fetchall()


def seed_demo_data():
    with get_connection() as conn:
        expense_count = conn.execute(
            "SELECT COUNT(*) AS count FROM expenses"
        ).fetchone()["count"]

        inventory_count = conn.execute(
            "SELECT COUNT(*) AS count FROM inventory"
        ).fetchone()["count"]

        if expense_count == 0:
            today = date.today()
            d1 = (today.replace(day=1) + timedelta(days=3)).isoformat()
            d2 = (today.replace(day=1) + timedelta(days=10)).isoformat()
            d3 = (today.replace(day=1) + timedelta(days=17)).isoformat()
            conn.executemany("""
                INSERT INTO expenses
                (expense_date, amount, category, programme, paid_by,
                 payment_method, notes, receipt_available)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (d1, 45000, "Transport", "Digital Skills", "Keh",
                 "Cash", "Transport for programme activity", 1),
                (d2, 85000, "Equipment", "STEM Programme", "Marius",
                 "Mobile Money", "Replacement equipment", 1),
                (d3, 25000, "Printing", "Digital Skills", "Keh",
                 "Cash", "Workshop handouts", 0),
            ])

        if inventory_count == 0:
            conn.executemany("""
                INSERT INTO inventory
                (item_name, quantity, programme, location,
                 responsible_person, condition, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [
                ("Laptop", 6, "Digital Skills", "Main Office", "Keh",
                 "Good", "Programme laptops"),
                ("Projector", 1, "STEM Programme", "Training Room", "Marius",
                 "Good", "Main presentation projector"),
                ("HDMI Cable", 1, "Digital Skills", "Main Office", "Keh",
                 "Low Quantity", "Only one working cable"),
                ("Tablet", 0, "Community Programme", "Field Office", "Aline",
                 "Missing", "Needs follow-up"),
            ])
