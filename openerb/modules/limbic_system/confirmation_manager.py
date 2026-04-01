"""Confirmation manager - Two-factor safety confirmation mechanism.

This module implements a two-stage confirmation system for high-risk actions,
requiring explicit confirmation before dangerous operations can proceed.
"""

import logging
from typing import Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ConfirmationStatus(Enum):
    """Status of a confirmation request."""

    PENDING = "pending"      # Awaiting confirmation
    CONFIRMED = "confirmed"  # User confirmed, can proceed
    REJECTED = "rejected"    # User rejected
    TIMEOUT = "timeout"      # Confirmation request expired


@dataclass
class ConfirmationRequest:
    """A request for user confirmation."""

    request_id: str
    action_name: str
    action_description: str
    risk_level: str
    risks: list
    strategies: list
    status: ConfirmationStatus
    created_at: datetime
    expires_at: datetime
    confirmed_at: Optional[datetime] = None
    confirmation_reason: Optional[str] = None


class ConfirmationManager:
    """Manage two-factor confirmation for high-risk actions.
    
    This manager ensures that high-risk actions require explicit
    user confirmation before execution, with timeout and audit features.
    
    Example:
        >>> manager = ConfirmationManager(timeout_seconds=30)
        >>> request = manager.request_confirmation(
        ...     action="jump",
        ...     description="Jump 0.5m height",
        ...     risk_level="RED"
        ... )
        >>> if manager.confirm(request.request_id, "OK for testing"):
        ...     execute_action()
    """

    def __init__(self, timeout_seconds: int = 30):
        """Initialize confirmation manager.

        Args:
            timeout_seconds: Seconds before confirmation expires
        """
        self.timeout_seconds = timeout_seconds
        self.pending_requests: dict = {}
        self.confirmation_history: list = []
        logger.debug(f"Initialized ConfirmationManager (timeout={timeout_seconds}s)")

    def request_confirmation(
        self,
        action_name: str,
        action_description: str,
        risk_level: str,
        risks: Optional[list] = None,
        strategies: Optional[list] = None,
        callback: Optional[Callable] = None,
    ) -> ConfirmationRequest:
        """Request user confirmation for an action.

        Args:
            action_name: Name of the action
            action_description: Human-readable description
            risk_level: Risk level (GREEN/YELLOW/RED)
            risks: List of identified risks
            strategies: List of mitigation strategies
            callback: Optional callback function on confirmation

        Returns:
            ConfirmationRequest object
        """
        import uuid

        request_id = str(uuid.uuid4())[:8]
        now = datetime.now()
        expires_at = now + timedelta(seconds=self.timeout_seconds)

        request = ConfirmationRequest(
            request_id=request_id,
            action_name=action_name,
            action_description=action_description,
            risk_level=risk_level,
            risks=risks or [],
            strategies=strategies or [],
            status=ConfirmationStatus.PENDING,
            created_at=now,
            expires_at=expires_at,
        )

        self.pending_requests[request_id] = {
            "request": request,
            "callback": callback,
        }

        logger.warning(
            f"Confirmation requested for {action_name}: {request_id}"
        )

        return request

    def confirm(
        self,
        request_id: str,
        reason: Optional[str] = None,
    ) -> bool:
        """Confirm a pending action.

        Args:
            request_id: ID of the confirmation request
            reason: Optional reason for confirmation

        Returns:
            True if confirmation was successful
        """
        if request_id not in self.pending_requests:
            logger.error(f"Unknown confirmation request: {request_id}")
            return False

        request_data = self.pending_requests[request_id]
        request = request_data["request"]

        # Check if request has expired
        if datetime.now() > request.expires_at:
            request.status = ConfirmationStatus.TIMEOUT
            logger.warning(f"Confirmation request {request_id} expired")
            return False

        # Mark as confirmed
        request.status = ConfirmationStatus.CONFIRMED
        request.confirmed_at = datetime.now()
        request.confirmation_reason = reason

        # Execute callback if provided
        if request_data["callback"]:
            try:
                request_data["callback"](request)
            except Exception as e:
                logger.error(f"Error in confirmation callback: {e}")

        # Record in history
        self.confirmation_history.append({
            "request_id": request_id,
            "action": request.action_name,
            "status": "confirmed",
            "reason": reason,
            "timestamp": request.confirmed_at,
        })

        logger.info(f"Confirmation approved: {request_id} ({request.action_name})")
        return True

    def reject(
        self,
        request_id: str,
        reason: Optional[str] = None,
    ) -> bool:
        """Reject a pending confirmation.

        Args:
            request_id: ID of the confirmation request
            reason: Optional reason for rejection

        Returns:
            True if rejection was successful
        """
        if request_id not in self.pending_requests:
            logger.error(f"Unknown confirmation request: {request_id}")
            return False

        request_data = self.pending_requests[request_id]
        request = request_data["request"]

        # Mark as rejected
        request.status = ConfirmationStatus.REJECTED
        request.confirmation_reason = reason

        # Record in history
        self.confirmation_history.append({
            "request_id": request_id,
            "action": request.action_name,
            "status": "rejected",
            "reason": reason,
            "timestamp": datetime.now(),
        })

        logger.info(f"Confirmation rejected: {request_id} ({request.action_name})")
        return True

    def get_request(self, request_id: str) -> Optional[ConfirmationRequest]:
        """Get a confirmation request by ID.

        Args:
            request_id: ID of the request

        Returns:
            ConfirmationRequest if found, None otherwise
        """
        if request_id in self.pending_requests:
            return self.pending_requests[request_id]["request"]
        return None

    def get_pending_requests(self) -> list:
        """Get all pending confirmation requests.

        Returns:
            List of pending ConfirmationRequest objects
        """
        pending = []
        now = datetime.now()

        for request_id, request_data in self.pending_requests.items():
            request = request_data["request"]

            # Check timeout
            if now > request.expires_at:
                request.status = ConfirmationStatus.TIMEOUT
            elif request.status == ConfirmationStatus.PENDING:
                pending.append(request)

        return pending

    def is_confirmed(self, request_id: str) -> bool:
        """Check if a request is confirmed.

        Args:
            request_id: ID of the request

        Returns:
            True if confirmed, False otherwise
        """
        request = self.get_request(request_id)
        if not request:
            return False
        return request.status == ConfirmationStatus.CONFIRMED

    def is_pending(self, request_id: str) -> bool:
        """Check if a request is still pending.

        Args:
            request_id: ID of the request

        Returns:
            True if pending, False otherwise
        """
        request = self.get_request(request_id)
        if not request:
            return False
        return request.status == ConfirmationStatus.PENDING

    def get_confirmation_history(self, last_n: Optional[int] = None) -> list:
        """Get confirmation history.

        Args:
            last_n: Return last N confirmations (None for all)

        Returns:
            List of confirmation records
        """
        if last_n is None:
            return self.confirmation_history.copy()
        return self.confirmation_history[-last_n:]

    def clear_pending_requests(self) -> int:
        """Clear all pending requests.

        Returns:
            Number of requests cleared
        """
        count = len(self.pending_requests)
        self.pending_requests.clear()
        logger.info(f"Cleared {count} pending requests")
        return count

    def get_confirmation_stats(self) -> dict:
        """Get confirmation statistics.

        Returns:
            Dictionary with confirmation stats
        """
        if not self.confirmation_history:
            return {
                "total_requests": 0,
                "confirmed": 0,
                "rejected": 0,
                "confirmation_rate": 0.0,
            }

        total = len(self.confirmation_history)
        confirmed = sum(
            1 for h in self.confirmation_history if h["status"] == "confirmed"
        )
        rejected = sum(
            1 for h in self.confirmation_history if h["status"] == "rejected"
        )

        return {
            "total_requests": total,
            "confirmed": confirmed,
            "rejected": rejected,
            "confirmation_rate": confirmed / total if total > 0 else 0.0,
        }
