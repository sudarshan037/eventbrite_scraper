# sqlite_handler.py
import aiosqlite


async def initialize_sqlite():
    """Initialize SQLite connection and create the table if it does not exist."""
    conn = await aiosqlite.connect("Scraper.db")
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS letsdo_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_url TEXT NOT NULL,
        url TEXT NOT NULL,
        sheet_name TEXT
    )
    """)
    await conn.commit()
    return conn


async def insert_into_sqlite(conn, source_url, urls, sheet_name):
    """Insert records into the SQLite database."""
    data = [(source_url, url, sheet_name) for url in urls]
    await conn.executemany(
        """INSERT INTO letsdo_events (source_url, url, sheet_name) VALUES (?, ?, ?)""",
        data
    )
    await conn.commit()
