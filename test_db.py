# test_db.py

import asyncio
import asyncpg

async def main():
    for host in ("127.0.0.1", "localhost"):
        try:
            conn = await asyncpg.connect(
                user="postgres",
                password="postgres",
                database="fraud_db",
                host=host,
                port=5433,
            )
            await conn.close()
            print(f"Connection successful via {host}")
        except Exception as e:
            print(f"Connection via {host} failed:", e)

if __name__ == "__main__":
    asyncio.run(main())
