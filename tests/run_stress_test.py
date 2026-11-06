
import os
import sqlite3

from edip import EDIPEngine


# ============================================================
# 1. DATABASE CONFIGURATION
# ============================================================

DB = "factory_erp.db"

conn = sqlite3.connect(DB)

conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA foreign_keys = ON;")


# ============================================================
# 2. CREATE DATABASE TABLES
# ============================================================

conn.execute("""
    CREATE TABLE IF NOT EXISTS Suppliers (
        supplier_id INTEGER PRIMARY KEY,
        supplier_name TEXT
    );
""")

conn.execute("""
    CREATE TABLE IF NOT EXISTS Invoices (
        invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT UNIQUE NOT NULL,
        supplier_id INTEGER NOT NULL,
        total_amount REAL NOT NULL CHECK(total_amount > 0),

        FOREIGN KEY (supplier_id)
            REFERENCES Suppliers(supplier_id)
    );
""")


# ============================================================
# 3. SEED SUPPLIER DATA
# ============================================================

conn.executemany(
    """
    INSERT OR IGNORE INTO Suppliers
    VALUES (?, ?);
    """,
    [
        (101, "Lyrox Raw Materials"),
        (102, "Crestline Logistics"),
        (103, "Zosix Steel")
    ]
)

conn.commit()
conn.close()


# ============================================================
# 4. INITIALIZE EDIP ENGINE
# ============================================================

engine = EDIPEngine(
    db_path=DB,
    target_tables=["Invoices"],
    model="llama3.2:1b",
    archive_dir="./Processed_Archive",
    quarantine_dir="./Quarantine_Documents"
)


# ============================================================
# 5. PROCESS INBOUND DOCUMENTS
# ============================================================

INBOUND_DIR = "./Inbound_Invoices"

for filename in os.listdir(INBOUND_DIR):

    if filename.lower().endswith(".pdf"):

        file_path = os.path.join(
            INBOUND_DIR,
            filename
        )

        success, details = engine.ingest_document(
            file_path
        )

        status = "ARCHIVED" if success else "QUARANTINED"

        print(
            f"File: {filename} | Status: {status}"
        )
