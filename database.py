# Database connection and operations
import aiosqlite
import json
from datetime import datetime

DB_PATH = "tedred_leads.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
                name TEXT,
                email TEXT,
                phone TEXT,
                interest TEXT,
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TEXT
            )
        """)
        await db.commit()

async def save_lead(session_id: str, name=None, email=None, phone=None, interest=None):
    # Save to SQLite as before
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO leads (session_id, name, email, phone, interest, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                name = COALESCE(excluded.name, name),
                email = COALESCE(excluded.email, email),
                phone = COALESCE(excluded.phone, phone),
                interest = COALESCE(excluded.interest, interest)
        """, (session_id, name, email, phone, interest, datetime.utcnow().isoformat()))
        await db.commit()

    # Also save to Google Sheets
    try:
        import asyncio
        from sheets import append_lead
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: append_lead(
            session_id=session_id,
            name=name,
            email=email,
            phone=phone,
            interest=interest
        ))
    except Exception as e:
        print(f"DEBUG: Sheets sync error: {e}")

async def save_message(session_id: str, role: str, content: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO conversations (session_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (session_id, role, content, datetime.utcnow().isoformat()))
        await db.commit()

async def get_history(session_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT role, content FROM conversations
            WHERE session_id = ?
            ORDER BY id ASC
        """, (session_id,))
        rows = await cursor.fetchall()
        return [{"role": r[0], "content": r[1]} for r in rows]

async def get_all_leads():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT id, session_id, name, email, phone, interest, created_at
            FROM leads ORDER BY id DESC
        """)
        rows = await cursor.fetchall()
        return [
            {"id": r[0], "session_id": r[1], "name": r[2],
             "email": r[3], "phone": r[4], "interest": r[5], "created_at": r[6]}
            for r in rows
        ]