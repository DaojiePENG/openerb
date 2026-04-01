"""Learning History Tracker - Track and analyze learning history."""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from openerb.core.types import ExecutionResult

logger = logging.getLogger(__name__)


@dataclass
class LearningEvent:
    """A single learning event/execution."""
    event_id: str
    skill_id: str
    skill_name: str
    user_id: str
    timestamp: datetime
    duration: float  # seconds
    success: bool
    confidence_before: float
    confidence_after: float
    execution_result: Optional[str] = None
    error_message: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""


@dataclass
class LearningSession:
    """A learning session containing multiple events."""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0  # seconds
    events: List[LearningEvent] = field(default_factory=list)
    focus_skill: Optional[str] = None
    session_success_rate: float = 0.0
    notes: str = ""


class LearningHistoryTracker:
    """Track and analyze learning history."""
    
    def __init__(self, retention_days: int = 365):
        """Initialize history tracker.
        
        Args:
            retention_days: How long to keep history (default: 1 year)
        """
        self.retention_days = retention_days
        self.events: Dict[str, LearningEvent] = {}
        self.sessions: Dict[str, LearningSession] = {}
        self.current_session: Optional[LearningSession] = None
        logger.info(f"LearningHistoryTracker initialized (retention: {retention_days} days)")
    
    def start_session(self, user_id: str, focus_skill: Optional[str] = None) -> LearningSession:
        """Start a new learning session.
        
        Args:
            user_id: User ID
            focus_skill: Optional skill to focus on
        
        Returns:
            Started LearningSession
        """
        session_id = f"session_{datetime.now().timestamp()}"
        session = LearningSession(
            session_id=session_id,
            user_id=user_id,
            start_time=datetime.now(),
            focus_skill=focus_skill
        )
        
        self.sessions[session_id] = session
        self.current_session = session
        
        logger.info(f"Started learning session {session_id} for {user_id}")
        
        return session
    
    def end_session(self) -> Optional[LearningSession]:
        """End current learning session.
        
        Returns:
            Ended LearningSession or None
        """
        if not self.current_session:
            logger.warning("No active session to end")
            return None
        
        session = self.current_session
        session.end_time = datetime.now()
        session.duration = (session.end_time - session.start_time).total_seconds()
        
        # Calculate session success rate
        if session.events:
            successes = sum(1 for e in session.events if e.success)
            session.session_success_rate = successes / len(session.events)
        
        self.current_session = None
        
        logger.info(f"Ended session {session.session_id} with {len(session.events)} events")
        
        return session
    
    def record_event(
        self,
        skill_id: str,
        skill_name: str,
        user_id: str,
        duration: float,
        success: bool,
        confidence_before: float,
        confidence_after: float,
        execution_result: Optional[str] = None,
        error_message: Optional[str] = None,
        parameters: Optional[Dict] = None,
        context: Optional[Dict] = None,
        notes: str = ""
    ) -> LearningEvent:
        """Record a learning event.
        
        Args:
            skill_id: Skill ID
            skill_name: Skill name
            user_id: User ID
            duration: Duration in seconds
            success: Whether execution was successful
            confidence_before: Confidence before execution
            confidence_after: Confidence after execution
            execution_result: Optional result details
            error_message: Optional error message
            parameters: Optional execution parameters
            context: Optional context information
            notes: Optional notes
        
        Returns:
            Created LearningEvent
        """
        event_id = f"event_{datetime.now().timestamp()}"
        event = LearningEvent(
            event_id=event_id,
            skill_id=skill_id,
            skill_name=skill_name,
            user_id=user_id,
            timestamp=datetime.now(),
            duration=duration,
            success=success,
            confidence_before=confidence_before,
            confidence_after=confidence_after,
            execution_result=execution_result,
            error_message=error_message,
            parameters=parameters or {},
            context=context or {},
            notes=notes
        )
        
        self.events[event_id] = event
        
        # Add to current session if active
        if self.current_session:
            self.current_session.events.append(event)
        
        logger.debug(f"Recorded event {event_id}: {skill_name} {'success' if success else 'failed'}")
        
        return event
    
    def get_event(self, event_id: str) -> Optional[LearningEvent]:
        """Get event by ID.
        
        Args:
            event_id: Event ID
        
        Returns:
            LearningEvent or None
        """
        return self.events.get(event_id)
    
    def get_session(self, session_id: str) -> Optional[LearningSession]:
        """Get session by ID.
        
        Args:
            session_id: Session ID
        
        Returns:
            LearningSession or None
        """
        return self.sessions.get(session_id)
    
    def get_user_history(
        self,
        user_id: str,
        days: Optional[int] = None,
        skill_id: Optional[str] = None,
        limit: int = 100
    ) -> List[LearningEvent]:
        """Get learning history for user.
        
        Args:
            user_id: User ID
            days: Optional days to look back
            skill_id: Optional skill filter
            limit: Maximum events to return
        
        Returns:
            List of LearningEvent
        """
        events = [e for e in self.events.values() if e.user_id == user_id]
        
        # Filter by time
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            events = [e for e in events if e.timestamp >= cutoff]
        
        # Filter by skill
        if skill_id:
            events = [e for e in events if e.skill_id == skill_id]
        
        # Sort by timestamp descending
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        return events[:limit]
    
    def get_skill_history(
        self,
        skill_id: str,
        user_id: Optional[str] = None,
        days: Optional[int] = None
    ) -> List[LearningEvent]:
        """Get history for specific skill.
        
        Args:
            skill_id: Skill ID
            user_id: Optional user filter
            days: Optional days to look back
        
        Returns:
            List of LearningEvent
        """
        events = [e for e in self.events.values() if e.skill_id == skill_id]
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            events = [e for e in events if e.timestamp >= cutoff]
        
        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp)
        
        return events
    
    def get_session_history(self, user_id: str, limit: int = 10) -> List[LearningSession]:
        """Get session history for user.
        
        Args:
            user_id: User ID
            limit: Maximum sessions to return
        
        Returns:
            List of LearningSession
        """
        sessions = [s for s in self.sessions.values() if s.user_id == user_id and s.end_time]
        
        # Sort by end_time descending
        sessions.sort(key=lambda s: s.end_time or datetime.now(), reverse=True)
        
        return sessions[:limit]
    
    def get_learning_stats(
        self,
        user_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get learning statistics for time period.
        
        Args:
            user_id: User ID
            days: Days to look back
        
        Returns:
            Dict with statistics
        """
        events = self.get_user_history(user_id, days=days, limit=1000)
        
        if not events:
            return {
                "user_id": user_id,
                "period_days": days,
                "total_events": 0,
                "success_rate": 0.0
            }
        
        successes = sum(1 for e in events if e.success)
        total_duration = sum(e.duration for e in events)
        avg_confidence_gain = sum(
            e.confidence_after - e.confidence_before
            for e in events
        ) / len(events) if events else 0.0
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_events": len(events),
            "success_rate": successes / len(events) if events else 0.0,
            "successes": successes,
            "failures": len(events) - successes,
            "total_duration": total_duration,
            "average_event_duration": total_duration / len(events) if events else 0.0,
            "average_confidence_gain": avg_confidence_gain,
            "unique_skills_practiced": len(set(e.skill_id for e in events)),
            "most_practiced_skill": (
                max(set(e.skill_id for e in events), 
                    key=[e.skill_id for e in events].count)
                if events else None
            )
        }
    
    def get_skill_analytics(
        self,
        skill_id: str,
        user_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get analytics for specific skill.
        
        Args:
            skill_id: Skill ID
            user_id: Optional user filter
            days: Days to look back
        
        Returns:
            Dict with analytics
        """
        events = self.get_skill_history(skill_id, user_id=user_id, days=days)
        
        if not events:
            return {
                "skill_id": skill_id,
                "total_executions": 0,
                "success_rate": 0.0
            }
        
        successes = sum(1 for e in events if e.success)
        failures = len(events) - successes
        avg_duration = sum(e.duration for e in events) / len(events)
        
        # Trend analysis: compare first half vs second half
        mid_point = len(events) // 2
        first_half = events[:mid_point]
        second_half = events[mid_point:]
        
        first_half_success = (
            sum(1 for e in first_half if e.success) / len(first_half)
            if first_half else 0.0
        )
        second_half_success = (
            sum(1 for e in second_half if e.success) / len(second_half)
            if second_half else 0.0
        )
        
        improving = second_half_success > first_half_success
        
        return {
            "skill_id": skill_id,
            "total_executions": len(events),
            "successes": successes,
            "failures": failures,
            "success_rate": successes / len(events) if events else 0.0,
            "average_duration": avg_duration,
            "average_confidence_gain": (
                sum(e.confidence_after - e.confidence_before for e in events) / len(events)
                if events else 0.0
            ),
            "improving": improving,
            "trend": "improving" if improving else "declining"
        }
    
    def cleanup_old_history(self, retention_days: Optional[int] = None) -> int:
        """Remove old history events.
        
        Args:
            retention_days: Days to keep (uses default if None)
        
        Returns:
            Number of events removed
        """
        cutoff = datetime.now() - timedelta(days=retention_days or self.retention_days)
        
        events_to_remove = [
            eid for eid, event in self.events.items()
            if event.timestamp < cutoff
        ]
        
        for eid in events_to_remove:
            del self.events[eid]
        
        logger.info(f"Cleaned up {len(events_to_remove)} old events")
        
        return len(events_to_remove)
    
    def export_history(
        self,
        user_id: str,
        format: str = "json"
    ) -> str:
        """Export user's learning history.
        
        Args:
            user_id: User ID
            format: Export format ("json" or "csv")
        
        Returns:
            Exported history as string
        """
        events = self.get_user_history(user_id, limit=10000)
        
        if format == "json":
            import json
            return json.dumps(
                [
                    {
                        "event_id": e.event_id,
                        "skill_id": e.skill_id,
                        "skill_name": e.skill_name,
                        "timestamp": e.timestamp.isoformat(),
                        "duration": e.duration,
                        "success": e.success,
                        "confidence_before": e.confidence_before,
                        "confidence_after": e.confidence_after
                    }
                    for e in events
                ],
                indent=2
            )
        
        elif format == "csv":
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow([
                "event_id", "skill_id", "skill_name", "timestamp",
                "duration", "success", "confidence_before", "confidence_after"
            ])
            
            for e in events:
                writer.writerow([
                    e.event_id, e.skill_id, e.skill_name, e.timestamp.isoformat(),
                    e.duration, e.success, e.confidence_before, e.confidence_after
                ])
            
            return output.getvalue()
        
        return ""
