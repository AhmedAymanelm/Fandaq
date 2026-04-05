import aiosmtplib
from email.message import EmailMessage
from typing import Optional
from app.config import get_settings

async def send_email_with_attachment(
    to_email: str,
    subject: str,
    body_text: str,
    attachment_name: Optional[str] = None,
    attachment_bytes: Optional[bytes] = None,
):
    """
    Sends an email with an Excel (.xlsx) attachment.
    """
    settings = get_settings()
    
    smtp_host = settings.SMTP_HOST
    smtp_port = settings.SMTP_PORT
    smtp_user = settings.SMTP_USER
    smtp_password = settings.SMTP_PASSWORD
    sender_email = settings.SENDER_EMAIL or smtp_user

    if not smtp_user or not smtp_password:
        raise ValueError("SMTP variables (SMTP_USER, SMTP_PASSWORD) are not configured. Email sending is disabled.")

    msg = EmailMessage()
    # Using a professional display name helps avoid Spam filters
    display_name = settings.APP_NAME or "RAHATY"
    msg['From'] = f'"{display_name}" <{sender_email}>'
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.set_content(body_text)

    # Attach a file only when both name and bytes are provided.
    if attachment_name and attachment_bytes is not None:
        msg.add_attachment(
            attachment_bytes,
            maintype='application',
            subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=attachment_name
        )

    # Send email
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"📧 Attempting to send email to {to_email} via {smtp_host}:{smtp_port} (User: {smtp_user})")
        
        if smtp_port == 465:
            # TLS
            await aiosmtplib.send(
                msg,
                hostname=smtp_host,
                port=smtp_port,
                username=smtp_user,
                password=smtp_password,
                use_tls=True
            )
        else:
            # STARTTLS
            await aiosmtplib.send(
                msg,
                hostname=smtp_host,
                port=smtp_port,
                username=smtp_user,
                password=smtp_password,
                start_tls=True
            )
        logger.info(f"✅ Email sent successfully to {to_email}")
    except Exception as e:
        logger.error(f"❌ Email sending failed for {to_email}: {str(e)}")
        raise e
