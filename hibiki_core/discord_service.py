import aiohttp
import json
import re
from typing import Dict, Any, Optional

# Use relative imports for package
try:
    from .config import config as settings
except ImportError:
    from app.core.config import settings

try:
    from .logger import get_logger
except ImportError:
    from app.core.logger import get_logger

logger = get_logger("hibiki_core.discord")


def anonymize_email(email: str) -> str:
    """
    Anonymize an email address while keeping it identifiable

    Examples:
        john.doe@example.com -> j***.d***@example.com
        user@domain.com -> u***@domain.com
        test.user@company.org -> t***.u***@company.org

    Args:
        email: The email address to anonymize

    Returns:
        str: The anonymized email address
    """
    if not email or "@" not in email:
        return email

    try:
        # Split email into local and domain parts
        local_part, domain = email.split("@", 1)

        # Anonymize local part
        if "." in local_part:
            # Handle emails with dots: john.doe -> j***.d***
            parts = local_part.split(".")
            anonymized_parts = []
            for part in parts:
                if len(part) > 1:
                    anonymized_parts.append(f"{part[0]}***")
                else:
                    anonymized_parts.append(part)
            anonymized_local = ".".join(anonymized_parts)
        else:
            # Handle emails without dots: user -> u***
            if len(local_part) > 1:
                anonymized_local = f"{local_part[0]}***"
            else:
                anonymized_local = local_part

        return f"{anonymized_local}@{domain}"

    except Exception as e:
        logger.error(f"Error anonymizing email {email}: {str(e)}")
        return email  # Return original if anonymization fails


async def send_discord_notification(
    message: str,
    webhook_url: str,
    username: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> bool:
    """
    Send a notification to Discord using a webhook

    Args:
        message: The message to send
        webhook_url: Discord webhook URL
        username: Optional username for the webhook
        avatar_url: Optional avatar URL for the webhook

    Returns:
        bool: True if successful, False otherwise
    """
    if not webhook_url:
        logger.warning("Discord webhook URL is not configured")
        return False

    payload = {"content": message}

    if username:
        payload["username"] = username

    if avatar_url:
        payload["avatar_url"] = avatar_url

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 204:
                    logger.info("Discord notification sent successfully")
                    return True
                else:
                    logger.error(
                        f"Failed to send Discord notification. Status: {response.status}"
                    )
                    return False
    except Exception as e:
        logger.error(f"Error sending Discord notification: {str(e)}")
        return False


async def send_user_signup_notification(
    email: str,
    webhook_url: str,
    message_template: str = "🎉 New user signed up: {email}",
    username: Optional[str] = None,
) -> bool:
    """
    Send a notification when a new user signs up

    Args:
        email: The email of the new user
        webhook_url: Discord webhook URL
        message_template: Template for the message
        username: Custom username for the webhook (optional)

    Returns:
        bool: True if successful, False otherwise
    """
    # Anonymize the email for privacy
    anonymized_email = anonymize_email(email)
    message = message_template.format(email=anonymized_email)

    return await send_discord_notification(
        message=message,
        webhook_url=webhook_url,
        username=username or "SoundLocal Bot",  # Use provided username or default
        avatar_url="https://cdn.discordapp.com/emojis/🎉.png",
    )


async def send_notification_by_type(
    notification_type: str, webhook_url: str, message_template: str, **template_vars
) -> bool:
    """
    Send a notification for any notification type with template variables

    Args:
        notification_type: Type of notification (e.g., "user_signup", "subscription", "log")
        webhook_url: Discord webhook URL
        message_template: Template for the message
        **template_vars: Variables to substitute in the template

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Anonymize email if it's in the template variables
        if "email" in template_vars:
            template_vars["email"] = anonymize_email(template_vars["email"])

        message = message_template.format(**template_vars)
        return await send_discord_notification(
            message=message, webhook_url=webhook_url, username="SoundLocal Bot"
        )
    except KeyError as e:
        logger.error(
            f"Missing template variable {e} for notification type {notification_type}"
        )
        return False
    except Exception as e:
        logger.error(
            f"Error formatting notification for type {notification_type}: {str(e)}"
        )
        return False


async def send_error_notification(
    level: str,
    message: str,
    logger_name: str,
    webhook_url: str,
    username: Optional[str] = None,
    trace: Optional[str] = None,
    user_id: Optional[str] = None,
    path: Optional[str] = None,
    method: Optional[str] = None,
) -> bool:
    """
    Send an error notification to Discord with formatted details
    
    Args:
        level: Log level (ERROR, CRITICAL)
        message: Error message
        logger_name: Name of the logger
        webhook_url: Discord webhook URL
        username: Custom username for the webhook (optional)
        trace: Optional stack trace
        user_id: Optional user ID
        path: Optional request path
        method: Optional HTTP method
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Truncate message if too long (Discord limit is 2000 chars)
    truncated_message = message[:500] if len(message) > 500 else message
    
    # Build the notification message
    discord_message = f"**{level}** in `{logger_name}`\n"
    discord_message += f"```\n{truncated_message}\n```"
    
    if path:
        discord_message += f"\n**Path:** `{path}`"
    if method:
        discord_message += f" **Method:** `{method}`"
    if user_id:
        discord_message += f"\n**User ID:** `{user_id}`"
    
    if trace:
        # Truncate trace if too long
        truncated_trace = trace[:800] if len(trace) > 800 else trace
        discord_message += f"\n**Trace:**\n```\n{truncated_trace}\n```"
    
    # Ensure total message doesn't exceed Discord's limit
    if len(discord_message) > 1900:
        discord_message = discord_message[:1900] + "\n...(truncated)"
    
    return await send_discord_notification(
        message=discord_message,
        webhook_url=webhook_url,
        username=username or "SoundLocal Error Bot"
    )
