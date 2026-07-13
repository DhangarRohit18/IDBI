"""
FinTwin AI — Notification Celery Tasks
"""

from __future__ import annotations

import asyncio

import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(
    name="app.tasks.notification_tasks.send_email",
    max_retries=3,
    default_retry_delay=60,
    queue="notification_queue",
)
def send_email_task(
    to_email: str,
    to_name: str,
    subject: str,
    template_name: str,
    template_data: dict,
) -> dict:
    """Send an email notification via SendGrid."""
    return asyncio.get_event_loop().run_until_complete(
        _async_send_email(to_email, to_name, subject, template_name, template_data)
    )


async def _async_send_email(
    to_email: str,
    to_name: str,
    subject: str,
    template_name: str,
    template_data: dict,
) -> dict:
    from app.integrations.sendgrid_client import SendGridClient
    client = SendGridClient()
    success = await client.send_templated_email(
        to_email=to_email,
        to_name=to_name,
        subject=subject,
        template_name=template_name,
        template_data=template_data,
    )
    return {"success": success, "to_email": to_email}


@celery_app.task(
    name="app.tasks.notification_tasks.send_sms",
    max_retries=3,
    queue="notification_queue",
)
def send_sms_task(to_number: str, message: str) -> dict:
    """Send SMS via Twilio."""
    return asyncio.get_event_loop().run_until_complete(
        _async_send_sms(to_number, message)
    )


async def _async_send_sms(to_number: str, message: str) -> dict:
    from app.integrations.twilio_client import TwilioClient
    client = TwilioClient()
    success = await client.send_sms(to_number, message)
    return {"success": success, "to": to_number}


@celery_app.task(
    name="app.tasks.report_tasks.refresh_portfolio_cache",
    queue="notification_queue",
)
def refresh_portfolio_cache() -> dict:
    """Refresh portfolio summary cache for all tenants."""
    return asyncio.get_event_loop().run_until_complete(
        _async_refresh_portfolio_cache()
    )


async def _async_refresh_portfolio_cache() -> dict:
    from app.db.base import AsyncSessionLocal
    from app.models.tenant import Tenant
    from app.services.portfolio_service import PortfolioService
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Tenant).where(Tenant.is_active == True))
        tenants = result.scalars().all()
        service = PortfolioService(db)
        for tenant in tenants:
            await service.get_summary(str(tenant.id), force_refresh=True)
    return {"tenants_refreshed": len(tenants)}
