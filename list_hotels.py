import asyncio
from app.database import async_session_factory
from app.models.hotel import Hotel
from sqlalchemy import select

async def main():
    async with async_session_factory() as db:
        res = await db.execute(select(Hotel))
        hotels = res.scalars().all()
        for h in hotels:
            print(f"ID: {h.id}, Name: {h.name}, Owner Email: {h.owner_email}")

asyncio.run(main())
