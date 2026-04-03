"""
WhatsApp & Telegram webhook payload parser — extracts messages from incoming payloads.
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ParsedMessage:
    """Parsed message from WhatsApp or Telegram."""
    message_id: str
    sender_phone: str          # WhatsApp phone or Telegram chat ID
    recipient_phone_id: str    # WhatsApp phone_number_id or Telegram bot username
    text: str                  # Message text content
    timestamp: str
    sender_name: str = ""
    source: str = "whatsapp"   # "whatsapp" or "telegram"


def parse_webhook_payload(payload: dict) -> list[ParsedMessage]:
    """
    Parse a Meta WhatsApp webhook payload.

    Returns:
        List of ParsedMessage objects. Empty list if no text messages found.
    """
    return _parse_whatsapp_payload(payload)


def parse_telegram_update(update: dict) -> list[ParsedMessage]:
    """
    Parse a Telegram Bot API Update object.

    Telegram Update structure:
    {
      "update_id": 123456,
      "message": {
        "message_id": 789,
        "from": {
          "id": 12345678,
          "first_name": "Ahmed",
          "last_name": "Ali",
          "username": "ahmed_ali"
        },
        "chat": {
          "id": 12345678,
          "type": "private"
        },
        "date": 1234567890,
        "text": "Hello"
      }
    }

    Returns:
        List of ParsedMessage objects. Empty list if no text messages found.
    """
    messages = []

    try:
        message = update.get("message")
        if not message:
            # Could be an edited_message, callback_query, etc. — skip
            return messages

        text = message.get("text")
        if not text:
            # Skip non-text messages (stickers, photos, etc.)
            return messages

        sender = message.get("from", {})
        chat = message.get("chat", {})

        # Build display name from first_name + last_name
        first_name = sender.get("first_name", "")
        last_name = sender.get("last_name", "")
        display_name = f"{first_name} {last_name}".strip()

        chat_id = str(chat.get("id", ""))
        message_id = str(message.get("message_id", ""))

        # Use update_id + message_id for unique dedup key
        unique_id = f"tg_{update.get('update_id', '')}_{message_id}"

        parsed = ParsedMessage(
            message_id=unique_id,
            sender_phone=chat_id,           # Telegram chat ID
            recipient_phone_id="telegram",  # Will be resolved from config
            text=text,
            timestamp=str(message.get("date", "")),
            sender_name=display_name,
            source="telegram",
        )
        messages.append(parsed)

    except Exception as e:
        logger.error(f"Error parsing Telegram update: {e}", exc_info=True)

    return messages


def _parse_whatsapp_payload(payload: dict) -> list[ParsedMessage]:
    """Parse WhatsApp Business webhook payload."""
    messages = []

    try:
        entries = payload.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                
                # Filter out status updates and other non-message events early
                if "messages" not in value:
                    continue

                metadata = value.get("metadata", {})
                phone_number_id = metadata.get("phone_number_id", "")

                # Get contact names
                contacts = value.get("contacts", [])
                contact_names = {}
                for contact in contacts:
                    wa_id = contact.get("wa_id", "")
                    name = contact.get("profile", {}).get("name", "")
                    contact_names[wa_id] = name

                # Parse messages (only text messages)
                raw_messages = value.get("messages", [])
                for msg in raw_messages:
                    msg_type = msg.get("type", "")
                    if msg_type != "text":
                        logger.info(f"Skipping non-text message type: {msg_type}")
                        continue

                    sender = msg.get("from", "")
                    parsed = ParsedMessage(
                        message_id=msg.get("id", ""),
                        sender_phone=sender,
                        recipient_phone_id=phone_number_id,
                        text=msg.get("text", {}).get("body", ""),
                        timestamp=msg.get("timestamp", ""),
                        sender_name=contact_names.get(sender, ""),
                        source="whatsapp",
                    )
                    messages.append(parsed)

    except Exception as e:
        logger.error(f"Error parsing WhatsApp payload: {e}", exc_info=True)

    return messages
