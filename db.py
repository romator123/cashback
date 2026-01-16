import aiosqlite
import logging

DB_NAME = "cashback.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cashbacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                bank TEXT NOT NULL,
                category TEXT NOT NULL,
                percent REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def add_cashback(user_id: int, bank: str, category: str, percent: float):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO cashbacks (user_id, bank, category, percent)
            VALUES (?, ?, ?, ?)
        """, (user_id, bank, category, percent))
        await db.commit()

async def get_best_cashback(user_id: int, category_query: str):
    """
    Search for cashback by category (partial match).
    Returns a list of tuples: (bank, category, percent)
    Sorted by percent DESC.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        # Use LIKE for partial match (e.g., "Food" matches "Fast Food")
        # Added % around query for wildcards
        query = f"%{category_query}%"
        async with db.execute("""
            SELECT bank, category, percent 
            FROM cashbacks 
            WHERE user_id = ? AND category LIKE ? 
            ORDER BY percent DESC
        """, (user_id, query)) as cursor:
            return await cursor.fetchall()

async def get_all_cashbacks(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT bank, category, percent 
            FROM cashbacks 
            WHERE user_id = ? 
            ORDER BY bank, percent DESC
        """, (user_id,)) as cursor:
            return await cursor.fetchall()

async def clear_cashbacks(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM cashbacks WHERE user_id = ?", (user_id,))
        await db.commit()
