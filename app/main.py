"""
Hotel WhatsApp SaaS — FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import get_settings
from app.api.webhook import router as webhook_router
from app.api.v1.hotels import router as hotels_router
from app.api.v1.rooms import router as rooms_router
from app.api.v1.reservations import router as reservations_router
from app.api.v1.expenses import router as expenses_router
from app.api.v1.reports import router as reports_router
from app.api.v1.complaints import router as complaints_router
from app.api.v1.guest_requests import router as guest_requests_router
from app.api.v1.guests import router as guests_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.daily_pricing import router as daily_pricing_router
from app.api.v1.competitors import router as competitors_router
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup
    print(f"🏨 {settings.APP_NAME} starting up...")
    
    # Start background scheduler (scraper + reminders)
    from app.services.scheduler import init_scheduler
    init_scheduler()
    
    # Ensure default admin exists
    from app.services.auth import AuthService
    from app.database import async_session_factory
    async with async_session_factory() as db:
        await AuthService.ensure_default_admin(db)
    
    
    yield
    # Shutdown
    print(f"🏨 {settings.APP_NAME} shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-hotel management system powered by WhatsApp, Telegram and AI",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────
# WhatsApp webhook (no prefix)
app.include_router(webhook_router, tags=["WhatsApp & Telegram Webhooks"])

# Admin API v1
prefix = settings.API_V1_PREFIX
app.include_router(auth_router, prefix=prefix, tags=["Authentication"])
app.include_router(hotels_router, prefix=prefix, tags=["Hotels"])
app.include_router(rooms_router, prefix=prefix, tags=["Rooms"])
app.include_router(reservations_router, prefix=prefix, tags=["Reservations"])
app.include_router(expenses_router, prefix=prefix, tags=["Expenses"])
app.include_router(reports_router, prefix=prefix, tags=["Reports"])
app.include_router(daily_pricing_router, prefix=prefix, tags=["Daily Pricing"])
app.include_router(competitors_router, prefix=prefix, tags=["Competitors"])
app.include_router(complaints_router, prefix=prefix, tags=["Complaints"])
app.include_router(guest_requests_router, prefix=prefix, tags=["Guest Requests"])
app.include_router(guests_router, prefix=prefix, tags=["Guests"])
app.include_router(reviews_router, prefix=prefix, tags=["Reviews"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

# ── Dashboard ─────────────────────────────────────────
dashboard_dir = os.path.join(os.path.dirname(__file__), "..", "dashboard")
if os.path.isdir(dashboard_dir):
    app.mount("/dashboard", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")
