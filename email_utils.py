from email.message import EmailMessage
import aiosmtplib
from config import settings
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

# Send email utility
async def send_email(
    to_email: str,
    subject: str,
    plain_text: str,
    html_content: str | None = None
) -> None:
    message = EmailMessage()

    message["From"] = settings.mail_from
    message["To"] = to_email
    message["Subject"] = subject

    message.set_content(plain_text)

    if html_content:
        message.add_alternative(html_content, subtype="html")

    await aiosmtplib.send(
        message,
        hostname=settings.mail_server,
        port=settings.mail_port,
        username=settings.mail_username if settings.mail_username else None,
        password=settings.mail_password.get_secret_value() or None,
        start_tls=settings.mail_use_tls
    )


# Send password reset email
async def send_password_reset_email(to_email: str, username: str, token: str) -> None:
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"

    template = templates.env.get_template("email/password-reset.html")
    html_content = template.render(reset_url=reset_url, username=username)

    plain_text = f"""Hi {username},
    You requested to reset your password. Click the link below to reset:
    {reset_url}

    This link will be expired in 1 hour.

    Thank you,
    FastAPI Blogs Team
    """

    await send_email(
        to_email=to_email,
        subject="Reset your FastAPI Blog password",
        plain_text=plain_text,
        html_content=html_content
    )