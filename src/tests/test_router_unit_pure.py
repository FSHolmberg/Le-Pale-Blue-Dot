import pytest
from src.router import Router
from src.history import MessageHistory


class TestCrisisDetection:
    """Test crisis pattern detection."""
    
    def setup_method(self):
        self.router = Router(history=MessageHistory())
    
    def test_detects_suicide_keywords(self):
        assert self.router._detect_crisis("I want to kill myself")
        assert self.router._detect_crisis("thinking about suicide")
        assert self.router._detect_crisis("end my life")
    
    def test_detects_self_harm(self):
        assert self.router._detect_crisis("going to hurt myself")
        assert self.router._detect_crisis("cut myself")
    
    def test_detects_violence_toward_others(self):
        assert self.router._detect_crisis("going to hurt someone")
        assert self.router._detect_crisis("kill my neighbor")
    
    def test_no_false_positives(self):
        assert not self.router._detect_crisis("I killed it at work today")
        assert not self.router._detect_crisis("this suicide mission of a project")
        assert not self.router._detect_crisis("hurt feelings")


class TestMuteLogic:
    """Test agent muting/unmuting."""
    
    def setup_method(self):
        self.router = Router(history=MessageHistory())
    
    def test_mute_bernie(self):
        result = self.router.mute_agent("bernie")
        assert "Bernie muted" in result
        assert "bernie" in self.router.muted_agents
    
    def test_cannot_mute_bart(self):
        result = self.router.mute_agent("bart")
        assert "essential" in result.lower()
        assert "bart" not in self.router.muted_agents
    
    def test_unmute_agent(self):
        self.router.muted_agents.add("bernie")
        result = self.router.unmute_agent("bernie")
        assert "unmuted" in result.lower()
        assert "bernie" not in self.router.muted_agents


class TestViolationScanning:
    """Test pre-route violation detection."""
    
    def setup_method(self):
        self.router = Router(history=MessageHistory())
    
    def test_empty_message_caught(self):
        has_violation, warning = self.router._pre_route_scan("   ")
        assert has_violation
        assert "speak" in warning.lower() or "pass" in warning.lower()
    
    def test_all_caps_caught(self):
        has_violation, warning = self.router._pre_route_scan("WHY IS EVERYTHING BROKEN")
        assert has_violation
    
    def test_normal_message_passes(self):
        has_violation, warning = self.router._pre_route_scan("hello there")
        assert not has_violation