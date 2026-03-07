"""
Database models for logging package.

Copy these to your project's database models file or use as-is.
"""

from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
import uuid


def create_log_model(Base):
    """
    Factory function to create Log model with your Base class.
    
    Usage:
        from hibiki_core.models import create_log_model
        
        Log = create_log_model(Base)
    """
    
    class Log(Base):
        __tablename__ = "logs"

        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        level = Column(String(20), nullable=False)
        message = Column(Text, nullable=False)
        logger_name = Column(String(255), nullable=False)
        user_id = Column(String(36), nullable=True)
        path = Column(String(255), nullable=True)
        method = Column(String(10), nullable=True)
        trace = Column(Text, nullable=True)
        created_at = Column(DateTime(timezone=True), server_default=func.now())

    return Log


def create_discord_config_model(Base):
    """
    Factory function to create DiscordNotificationConfig model.
    
    Usage:
        from hibiki_core.models import create_discord_config_model
        
        DiscordNotificationConfig = create_discord_config_model(Base)
    """
    
    class DiscordNotificationConfig(Base):
        __tablename__ = "discord_notification_config"

        id = Column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
        notification_type = Column(Text, nullable=False, index=True)
        webhook_url_encrypted = Column(Text, nullable=False)
        username = Column(Text, nullable=True)
        message_template = Column(Text, nullable=True)
        is_enabled = Column(Boolean, default=True)
        created_at = Column(DateTime(timezone=True), server_default=func.now())
        updated_at = Column(
            DateTime(timezone=True), 
            server_default=func.now(), 
            onupdate=func.now()
        )

    return DiscordNotificationConfig


# SQL for manual table creation
LOG_TABLE_SQL = """
CREATE TABLE logs (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    logger_name VARCHAR(255) NOT NULL,
    user_id VARCHAR(36),
    path VARCHAR(255),
    method VARCHAR(10),
    trace TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_logs_level ON logs(level);
CREATE INDEX idx_logs_logger_name ON logs(logger_name);
CREATE INDEX idx_logs_created_at ON logs(created_at);
"""

DISCORD_CONFIG_TABLE_SQL = """
CREATE TABLE discord_notification_config (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    notification_type TEXT NOT NULL,
    webhook_url_encrypted TEXT NOT NULL,
    username TEXT,
    message_template TEXT,
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_discord_notification_config_type 
ON discord_notification_config(notification_type);
"""
