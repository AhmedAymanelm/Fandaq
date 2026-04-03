"""
WhatsApp & Telegram API client — send messages via Meta Cloud API and Telegram Bot API.
"""

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class WhatsAppClient:
    """Client for sending messages via the Meta WhatsApp Business & Telegram Bot API."""

    def __init__(self):
        self.api_url = settings.WHATSAPP_API_URL
        self.api_token = settings.WHATSAPP_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def send_text_message(
        self,
        phone_number_id: str,
        to: str,
        message: str,
        api_token: str | None = None,
    ) -> dict:
        """
        Send a text message to a WhatsApp user.

        Args:
            phone_number_id: The hotel's WhatsApp Business phone number ID.
            to: Recipient phone number (with country code, e.g. '966501234567').
            message: The text message content.
            api_token: Per-hotel WhatsApp API token. Falls back to global token.

        Returns:
            API response dict.
        """
        token = api_token or self.api_token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        url = f"{self.api_url}/{phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": message},
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url, json=payload, headers=headers
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"Message sent to {to}: {data}")
                return data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"WhatsApp API error: {e.response.status_code} - {e.response.text}"
            )
            return {"error": str(e)}

        except Exception as e:
            logger.error(f"WhatsApp send error: {e}")
            return {"error": str(e)}

    async def send_telegram_message(
        self,
        bot_token: str,
        chat_id: str,
        message: str,
    ) -> dict:
        """
        Send a text message to a Telegram user via Telegram Bot API.

        Args:
            bot_token: The Telegram Bot API token.
            chat_id: The Telegram chat ID of the recipient.
            message: The text message content.

        Returns:
            API response dict.
        """
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                logger.info(f"Telegram message sent to {chat_id}: {data}")
                return data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Telegram API error: {e.response.status_code} - {e.response.text}"
            )
            return {"error": str(e)}

        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return {"error": str(e)}

    async def mark_as_read(
        self,
        phone_number_id: str,
        message_id: str,
        api_token: str | None = None,
    ) -> None:
        """Mark a message as read (blue ticks). WhatsApp only."""
        token = api_token or self.api_token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        url = f"{self.api_url}/{phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(url, json=payload, headers=headers)
        except Exception as e:
            logger.error(f"Failed to mark message as read: {e}")


# Singleton instance
whatsapp_client = WhatsAppClient()
