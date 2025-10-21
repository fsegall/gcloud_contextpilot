"""
Application Configuration
Centralized settings management for ContextPilot backend.
"""

import os
import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class StorageMode(str, Enum):
    """Storage backend mode."""

    LOCAL = "local"  # File-based storage (development)
    CLOUD = "cloud"  # Firestore (production)


class RewardsMode(str, Enum):
    """Rewards system mode."""

    FIRESTORE = "firestore"  # Off-chain Firestore
    BLOCKCHAIN = "blockchain"  # On-chain with Firestore backing


class EventBusMode(str, Enum):
    """Event bus mode."""

    IN_MEMORY = "in_memory"  # Local development
    PUBSUB = "pubsub"  # Google Pub/Sub


class AppConfig:
    """
    Application configuration loaded from environment variables.

    This provides explicit mode selection instead of silent fallbacks.
    """

    def __init__(self):
        # === Storage Configuration ===
        self.storage_mode = self._get_storage_mode()

        # === GCP Configuration ===
        self.gcp_project_id = os.getenv("GCP_PROJECT_ID")
        self.environment = os.getenv("ENVIRONMENT", "development")

        # === Rewards Configuration ===
        self.rewards_mode = self._get_rewards_mode()

        # === Event Bus Configuration ===
        self.event_bus_mode = self._get_event_bus_mode()

        # === API Keys ===
        self.gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.github_token = os.getenv("GITHUB_TOKEN")

        # === Blockchain (if blockchain rewards mode) ===
        self.polygon_rpc_url = os.getenv("POLYGON_RPC_URL")
        self.cpt_contract_address = os.getenv("CPT_CONTRACT_ADDRESS")
        self.minter_private_key = os.getenv("MINTER_PRIVATE_KEY")

        # Log configuration
        self._log_config()

    def _get_storage_mode(self) -> StorageMode:
        """
        Determine storage mode from environment.

        Priority:
        1. STORAGE_MODE env var (explicit)
        2. FIRESTORE_ENABLED (legacy, for backward compatibility)
        3. Default to LOCAL for development
        """
        # Check explicit STORAGE_MODE
        mode_str = os.getenv("STORAGE_MODE", "").lower()
        if mode_str in ["local", "cloud"]:
            return StorageMode(mode_str)

        # Legacy: check FIRESTORE_ENABLED
        if os.getenv("FIRESTORE_ENABLED", "").lower() == "true":
            logger.warning(
                "Using deprecated FIRESTORE_ENABLED. "
                "Please set STORAGE_MODE=cloud explicitly."
            )
            return StorageMode.CLOUD

        # Default to local
        logger.info("STORAGE_MODE not set. Defaulting to 'local'.")
        return StorageMode.LOCAL

    def _get_rewards_mode(self) -> RewardsMode:
        """Determine rewards mode from environment."""
        mode_str = os.getenv("REWARDS_MODE", "firestore").lower()

        if mode_str not in ["firestore", "blockchain"]:
            logger.warning(
                f"Invalid REWARDS_MODE='{mode_str}'. Defaulting to 'firestore'."
            )
            return RewardsMode.FIRESTORE

        return RewardsMode(mode_str)

    def _get_event_bus_mode(self) -> EventBusMode:
        """Determine event bus mode from environment."""
        # Check explicit EVENT_BUS_MODE first
        mode_str = os.getenv("EVENT_BUS_MODE", "").lower()
        if mode_str == "pubsub" and self.gcp_project_id:
            return EventBusMode.PUBSUB
        elif mode_str == "in_memory":
            return EventBusMode.IN_MEMORY

        # Legacy: check USE_PUBSUB
        use_pubsub = os.getenv("USE_PUBSUB", "").lower() == "true"
        if use_pubsub and self.gcp_project_id:
            logger.warning(
                "Using deprecated USE_PUBSUB. "
                "Please set EVENT_BUS_MODE=pubsub explicitly."
            )
            return EventBusMode.PUBSUB

        return EventBusMode.IN_MEMORY

    def _log_config(self):
        """Log current configuration (without sensitive data)."""
        logger.info("=" * 60)
        logger.info("ContextPilot Backend Configuration")
        logger.info("=" * 60)
        logger.info(f"Environment:        {self.environment}")
        logger.info(f"Storage Mode:       {self.storage_mode.value}")
        logger.info(f"Rewards Mode:       {self.rewards_mode.value}")
        logger.info(f"Event Bus Mode:     {self.event_bus_mode.value}")
        logger.info(f"GCP Project:        {self.gcp_project_id or 'Not Set'}")
        logger.info(
            f"Gemini API:         {'✓ Configured' if self.gemini_api_key else '✗ Missing'}"
        )
        logger.info(
            f"GitHub Token:       {'✓ Configured' if self.github_token else '✗ Missing'}"
        )
        logger.info("=" * 60)

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_cloud_storage(self) -> bool:
        """Check if using cloud storage (Firestore)."""
        return self.storage_mode == StorageMode.CLOUD

    @property
    def is_local_storage(self) -> bool:
        """Check if using local file storage."""
        return self.storage_mode == StorageMode.LOCAL

    @property
    def is_blockchain_rewards(self) -> bool:
        """Check if using blockchain rewards."""
        return self.rewards_mode == RewardsMode.BLOCKCHAIN

    @property
    def requires_gcp(self) -> bool:
        """Check if any feature requires GCP."""
        return (
            self.is_cloud_storage
            or self.event_bus_mode == EventBusMode.PUBSUB
            or self.is_blockchain_rewards  # Uses Firestore for pending tracking
        )

    def validate(self) -> list[str]:
        """
        Validate configuration and return list of errors.

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Check GCP requirements
        if self.requires_gcp and not self.gcp_project_id:
            errors.append(
                f"GCP_PROJECT_ID required for storage_mode={self.storage_mode.value}, "
                f"event_bus={self.event_bus_mode.value}"
            )

        # Check blockchain requirements
        if self.is_blockchain_rewards:
            if not self.polygon_rpc_url:
                errors.append("POLYGON_RPC_URL required for blockchain rewards")
            if not self.cpt_contract_address:
                errors.append("CPT_CONTRACT_ADDRESS required for blockchain rewards")
            if not self.minter_private_key:
                errors.append("MINTER_PRIVATE_KEY required for blockchain rewards")

        return errors


# Global config instance
_config: Optional[AppConfig] = None


def get_config(force_reload: bool = False) -> AppConfig:
    """
    Get application configuration singleton.

    Args:
        force_reload: Force reload from environment (for testing)

    Returns:
        AppConfig instance
    """
    global _config

    if _config is None or force_reload:
        _config = AppConfig()

        # Validate configuration
        errors = _config.validate()
        if errors:
            logger.error("Configuration errors:")
            for error in errors:
                logger.error(f"  - {error}")

            # In production, fail fast
            if _config.is_production:
                raise ValueError(f"Invalid configuration: {errors}")
            else:
                logger.warning("Continuing with invalid config in development mode")

    return _config


def reset_config():
    """Reset config singleton (for testing)."""
    global _config
    _config = None
