import asyncio
from app.database import async_session_factory
from app.models.daily_pricing import DailyPricing
from sqlalchemy import select
from datetime import date

async def main():
    async with async_session_factory() as db:
        res = await db.execute(select(DailyPricing).where(DailyPricing.date == date(2026, 4, 4)))
        prices = res.scalars().all()
        print(f"Prices found for 2026-04-04: {len(prices)}")
        for p in prices:
            print(f"- Hotel ID: {p.hotel_id}, Competitor: {p.competitor_hotel_name}")

asyncio.run(main())
