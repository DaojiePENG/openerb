"""Unit tests for Limbic System module."""

import pytest
from openerb.modules.limbic_system import (
    SafetyEvaluator,
    SafetyLevel,
    DangerAssessor,
    DangerLevel,
    ConfirmationManager,
    ConfirmationStatus,
)


class TestSafetyEvaluator:
    """Test SafetyEvaluator class."""

    @pytest.fixture
    def evaluator(self):
        """Create a SafetyEvaluator instance."""
        return SafetyEvaluator()

    def test_create_evaluator(self, evaluator):
        """Test creating a SafetyEvaluator."""
        assert evaluator is not None
        assert evaluator.strict_mode is False

    def test_evaluate_unknown_action(self, evaluator):
        """Test evaluating unknown action."""
        result = evaluator.evaluate_action("unknown_action")
        assert result.level == SafetyLevel.CAUTION
        assert result.passed is True

    def test_evaluate_high_risk_action(self, evaluator):
        """Test evaluating high-risk action."""
        result = evaluator.evaluate_action("jump")
        assert result.level == SafetyLevel.CAUTION
        assert len(result.recommendations) > 0 or "high-risk" in result.reason.lower()

    def test_evaluate_grasp_safe(self, evaluator):
        """Test safe grasp action."""
        result = evaluator.evaluate_action("grasp", {})
        assert result.passed is True

    def test_evaluate_grasp_excessive_force(self, evaluator):
        """Test grasp with excessive force."""
        result = evaluator.evaluate_action("grasp", {"force": 500.0})
        assert result.level in [SafetyLevel.DANGEROUS, SafetyLevel.CRITICAL]
        assert result.passed is False

    def test_can_execute_safe(self, evaluator):
        """Test can_execute for safe action."""
        can_exec = evaluator.can_execute("grasp", {})
        assert can_exec is True

    def test_can_execute_dangerous(self, evaluator):
        """Test can_execute for dangerous action."""
        can_exec = evaluator.can_execute("grasp", {"force": 500.0})
        assert can_exec is False

    def test_history_tracking(self, evaluator):
        """Test history tracking."""
        evaluator.evaluate_action("move", {})
        evaluator.evaluate_action("grasp", {})
        
        history = evaluator.get_evaluation_history()
        assert len(history) >= 2
        assert history[0]["action"] == "move"
        assert history[1]["action"] == "grasp"

    def test_clear_history(self, evaluator):
        """Test clearing history."""
        evaluator.evaluate_action("move", {})
        assert len(evaluator.get_evaluation_history()) > 0
        
        evaluator.clear_history()
        assert len(evaluator.get_evaluation_history()) == 0

    def test_safety_stats(self, evaluator):
        """Test safety statistics."""
        evaluator.evaluate_action("move", {})
        evaluator.evaluate_action("grasp", {"force": 500.0})
        
        stats = evaluator.get_safety_stats()
        assert "total_evaluations" in stats
        assert "safe_actions" in stats
        assert stats["total_evaluations"] == 2

    def test_strict_mode(self):
        """Test strict mode."""
        strict_eval = SafetyEvaluator(strict_mode=True)
        assert strict_eval.strict_mode is True

    def test_force_monitored_actions(self, evaluator):
        """Test force-monitored actions."""
        result = evaluator.evaluate_action("grasp", {"force": 20.0})
        assert result.passed is True


class TestDangerAssessor:
    """Test DangerAssessor class."""

    @pytest.fixture
    def assessor(self):
        """Create a DangerAssessor instance."""
        return DangerAssessor()

    def test_create_assessor(self, assessor):
        """Test creating a DangerAssessor."""
        assert assessor is not None

    def test_assess_safe_move(self, assessor):
        """Test assessing safe move."""
        result = assessor.assess_action("move", {})
        assert result.level == DangerLevel.GREEN
        assert 0 <= result.risk_score <= 100

    def test_assess_dangerous_push(self, assessor):
        """Test assessing dangerous push."""
        result = assessor.assess_action("push", {})
        assert result.level in [DangerLevel.YELLOW, DangerLevel.RED]
        assert result.requires_confirmation is True

    def test_risk_score_range(self, assessor):
        """Test that risk scores are in valid range."""
        actions = ["move", "grasp", "jump", "push"]
        for action in actions:
            result = assessor.assess_action(action, {})
            assert 0 <= result.risk_score <= 100

    def test_battery_multiplier(self, assessor):
        """Test low battery increases risk."""
        normal = assessor.assess_action("move", {})
        low_battery = assessor.assess_action("move", {"battery_level": 10})
        
        assert low_battery.risk_score >= normal.risk_score

    def test_stairs_multiplier(self, assessor):
        """Test stairs increase risk."""
        normal = assessor.assess_action("move", {})
        on_stairs = assessor.assess_action("move", {"location": "stairs"})
        
        assert on_stairs.risk_score >= normal.risk_score

    def test_mitigation_strategies(self, assessor):
        """Test mitigation strategy generation."""
        result = assessor.assess_action("push", {})
        assert isinstance(result.mitigation_strategies, list)
        if result.level == DangerLevel.RED:
            assert len(result.mitigation_strategies) > 0

    def test_primary_risks(self, assessor):
        """Test primary risks identification."""
        result = assessor.assess_action("jump", {})
        assert isinstance(result.primary_risks, list)

    def test_risk_comparison(self, assessor):
        """Test risk comparison."""
        actions = ["move", "grasp", "push"]
        comparison = assessor.get_risk_comparison(actions)
        
        assert len(comparison) == 3
        assert all("action" in item for item in comparison)
        assert all("risk_score" in item for item in comparison)

    def test_safest_action(self, assessor):
        """Test safest action selection."""
        actions = ["move", "push", "grasp"]
        safest = assessor.get_safest_action(actions)
        
        assert safest in ["move", "grasp", "push"]

    def test_danger_level_boundaries(self, assessor):
        """Test danger level classification."""
        green = assessor.assess_action("move", {})
        assert green.level == DangerLevel.GREEN
        assert green.risk_score < 40
        
        # Test RED boundary (push should be high risk)
        yellow_or_red = assessor.assess_action("push", {})
        assert yellow_or_red.level in [DangerLevel.YELLOW, DangerLevel.RED]
        assert yellow_or_red.risk_score > 40


class TestConfirmationManager:
    """Test ConfirmationManager class."""

    @pytest.fixture
    def manager(self):
        """Create a ConfirmationManager instance."""
        return ConfirmationManager(timeout_seconds=10)

    def test_create_manager(self, manager):
        """Test creating a ConfirmationManager."""
        assert manager is not None
        assert manager.timeout_seconds == 10

    def test_request_confirmation(self, manager):
        """Test requesting confirmation."""
        request = manager.request_confirmation(
            action_name="push",
            action_description="Push object",
            risk_level="RED"
        )
        
        assert request.request_id is not None
        assert request.action_name == "push"
        assert request.status == ConfirmationStatus.PENDING

    def test_confirm_action(self, manager):
        """Test confirming an action."""
        request = manager.request_confirmation(
            action_name="push",
            action_description="Push object",
            risk_level="RED"
        )
        
        result = manager.confirm(request.request_id)
        assert result is True
        assert manager.is_confirmed(request.request_id) is True

    def test_reject_action(self, manager):
        """Test rejecting an action."""
        request = manager.request_confirmation(
            action_name="push",
            action_description="Push object",
            risk_level="RED"
        )
        
        result = manager.reject(request.request_id)
        assert result is True
        assert request.status == ConfirmationStatus.REJECTED

    def test_get_pending_requests(self, manager):
        """Test getting pending requests."""
        manager.request_confirmation("action1", "desc1", "RED")
        manager.request_confirmation("action2", "desc2", "RED")
        
        pending = manager.get_pending_requests()
        assert len(pending) >= 2

    def test_confirmation_history(self, manager):
        """Test confirmation history."""
        req1 = manager.request_confirmation("action1", "desc1", "RED")
        req2 = manager.request_confirmation("action2", "desc2", "RED")
        
        manager.confirm(req1.request_id)
        manager.reject(req2.request_id)
        
        history = manager.get_confirmation_history()
        assert len(history) == 2

    def test_confirmation_stats(self, manager):
        """Test confirmation statistics."""
        req1 = manager.request_confirmation("action1", "desc1", "RED")
        req2 = manager.request_confirmation("action2", "desc2", "RED")
        
        manager.confirm(req1.request_id)
        manager.reject(req2.request_id)
        
        stats = manager.get_confirmation_stats()
        assert stats["total_requests"] == 2
        assert stats["confirmed"] == 1
        assert stats["rejected"] == 1

    def test_is_pending(self, manager):
        """Test is_pending check."""
        req = manager.request_confirmation("action", "desc", "RED")
        
        assert manager.is_pending(req.request_id) is True
        manager.confirm(req.request_id)
        assert manager.is_pending(req.request_id) is False

    def test_clear_pending_requests(self, manager):
        """Test clearing pending requests."""
        manager.request_confirmation("action1", "desc1", "RED")
        manager.request_confirmation("action2", "desc2", "RED")
        
        assert len(manager.get_pending_requests()) >= 2
        count = manager.clear_pending_requests()
        assert count >= 2


class TestIntegration:
    """Integration tests for safety system."""

    def test_workflow_safe_action(self):
        """Test workflow for safe action."""
        safety_eval = SafetyEvaluator()
        danger_assessor = DangerAssessor()
        
        safety_result = safety_eval.evaluate_action("move", {})
        danger_result = danger_assessor.assess_action("move", {})
        
        assert safety_result.passed is True
        assert danger_result.level == DangerLevel.GREEN
        assert danger_result.requires_confirmation is False

    def test_workflow_dangerous_action(self):
        """Test workflow for dangerous action."""
        safety_eval = SafetyEvaluator()
        danger_assessor = DangerAssessor()
        confirmation_manager = ConfirmationManager()
        
        safety_result = safety_eval.evaluate_action("push", {})
        danger_result = danger_assessor.assess_action("push", {})
        
        assert danger_result.level in [DangerLevel.YELLOW, DangerLevel.RED]
        assert danger_result.requires_confirmation is True
        
        if danger_result.requires_confirmation:
            request = confirmation_manager.request_confirmation(
                action_name="push",
                action_description="Push object",
                risk_level=danger_result.level.value,
                risks=danger_result.primary_risks,
                strategies=danger_result.mitigation_strategies
            )
            
            assert confirmation_manager.is_pending(request.request_id) is True
            confirmation_manager.confirm(request.request_id)
            assert confirmation_manager.is_confirmed(request.request_id) is True

    def test_full_system_integration(self):
        """Test full system integration with all three components."""
        safety_eval = SafetyEvaluator()
        danger_assessor = DangerAssessor()
        confirmation_manager = ConfirmationManager()
        
        actions = ["move", "grasp", "jump", "push"]
        
        for action in actions:
            safety_result = safety_eval.evaluate_action(action, {})
            danger_result = danger_assessor.assess_action(action, {})
            
            assert safety_result.level in [SafetyLevel.SAFE, SafetyLevel.CAUTION, SafetyLevel.DANGEROUS, SafetyLevel.CRITICAL]
            assert danger_result.level in [DangerLevel.GREEN, DangerLevel.YELLOW, DangerLevel.RED]
            
            if danger_result.requires_confirmation:
                request = confirmation_manager.request_confirmation(
                    action_name=action,
                    action_description=f"Perform {action}",
                    risk_level=danger_result.level.value
                )
                assert request.status == ConfirmationStatus.PENDING
        
        stats = safety_eval.get_safety_stats()
        assert stats["total_evaluations"] >= len(actions)
