import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from hibiki_core.discord_service import (
    anonymize_email,
    send_discord_notification,
    send_user_signup_notification,
    send_notification_by_type,
    send_error_notification,
)


class TestAnonymizeEmail:
    def test_simple_email(self):
        assert anonymize_email("user@domain.com") == "u***@domain.com"

    def test_dotted_email(self):
        assert anonymize_email("john.doe@example.com") == "j***.d***@example.com"

    def test_single_char_parts(self):
        assert anonymize_email("a.b@test.com") == "a.b@test.com"

    def test_empty_string(self):
        assert anonymize_email("") == ""

    def test_no_at_sign(self):
        assert anonymize_email("not-an-email") == "not-an-email"

    def test_none_input(self):
        assert anonymize_email(None) is None

    def test_triple_dotted(self):
        result = anonymize_email("first.middle.last@co.uk")
        assert result == "f***.m***.l***@co.uk"


class TestSendDiscordNotification:
    @pytest.mark.asyncio
    async def test_returns_false_without_url(self):
        result = await send_discord_notification(message="test", webhook_url="")
        assert result is False

    @pytest.mark.asyncio
    async def test_successful_send(self):
        mock_response = MagicMock()
        mock_response.status = 204

        mock_post_cm = AsyncMock()
        mock_post_cm.__aenter__.return_value = mock_response

        mock_session = MagicMock()
        mock_session.post.return_value = mock_post_cm

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_session)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_client):
            result = await send_discord_notification(
                message="test", webhook_url="https://discord.com/api/webhooks/test"
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_failed_send(self):
        mock_response = MagicMock()
        mock_response.status = 400

        mock_post_cm = AsyncMock()
        mock_post_cm.__aenter__.return_value = mock_response

        mock_session = MagicMock()
        mock_session.post.return_value = mock_post_cm

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_session)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_client):
            result = await send_discord_notification(
                message="test", webhook_url="https://discord.com/api/webhooks/test"
            )
            assert result is False


class TestSendErrorNotification:
    @pytest.mark.asyncio
    async def test_default_username(self):
        with patch(
            "hibiki_core.discord_service.send_discord_notification",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_send:
            await send_error_notification(
                level="ERROR",
                message="test error",
                logger_name="app.test",
                webhook_url="https://example.com/webhook",
            )
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs["username"] == "Hibiki Error Bot"

    @pytest.mark.asyncio
    async def test_custom_username(self):
        with patch(
            "hibiki_core.discord_service.send_discord_notification",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_send:
            await send_error_notification(
                level="ERROR",
                message="test error",
                logger_name="app.test",
                webhook_url="https://example.com/webhook",
                username="Custom Bot",
            )
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs["username"] == "Custom Bot"

    @pytest.mark.asyncio
    async def test_message_truncation(self):
        long_message = "x" * 600
        with patch(
            "hibiki_core.discord_service.send_discord_notification",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_send:
            await send_error_notification(
                level="ERROR",
                message=long_message,
                logger_name="app.test",
                webhook_url="https://example.com/webhook",
            )
            sent_message = mock_send.call_args[1]["message"]
            assert len(sent_message) <= 1950


class TestSendUserSignupNotification:
    @pytest.mark.asyncio
    async def test_default_username_is_hibiki(self):
        with patch(
            "hibiki_core.discord_service.send_discord_notification",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_send:
            await send_user_signup_notification(
                email="user@example.com",
                webhook_url="https://example.com/webhook",
            )
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs["username"] == "Hibiki Bot"
            assert "avatar_url" not in call_kwargs or call_kwargs["avatar_url"] is None


class TestSendNotificationByType:
    @pytest.mark.asyncio
    async def test_default_username_is_hibiki(self):
        with patch(
            "hibiki_core.discord_service.send_discord_notification",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_send:
            await send_notification_by_type(
                notification_type="test",
                webhook_url="https://example.com/webhook",
                message_template="Hello {name}",
                name="World",
            )
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs["username"] == "Hibiki Bot"

    @pytest.mark.asyncio
    async def test_custom_username(self):
        with patch(
            "hibiki_core.discord_service.send_discord_notification",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_send:
            await send_notification_by_type(
                notification_type="test",
                webhook_url="https://example.com/webhook",
                message_template="Hello {name}",
                username="My Bot",
                name="World",
            )
            call_kwargs = mock_send.call_args[1]
            assert call_kwargs["username"] == "My Bot"
