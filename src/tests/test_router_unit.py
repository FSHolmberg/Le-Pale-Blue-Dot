import pytest
from src.router import Router
from src.schemas.message import Message
from src.history import MessageHistory


class TestCrisisDetection:
    """Test crisis pattern detection."""
    
    def setup_method(self):
        """Create fresh router for each test."""
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


class TestRoutingDecisions:
    """Test which agent handles which input."""
    
    def setup_method(self):
        self.router = Router(history=MessageHistory())
    
    def test_crisis_routes_to_hermes(self):
        msg = Message(user_id="test", text="I want to hurt myself", timestamp=123)
        agent, reply = self.router.handle(msg)
        assert agent == "hermes"
    
    def test_all_caps_routes_to_blanca(self):
        msg = Message(user_id="test", text="WHY IS EVERYTHING BROKEN", timestamp=123)
        agent, reply = self.router.handle(msg)
        assert agent == "blanca"
    
    def test_jb_prefix_routes_to_jb(self):
        msg = Message(user_id="test", text="jb what do you think", timestamp=123)
        agent, reply = self.router.handle(msg)
        assert agent == "jb"
    
    def test_default_routes_to_bart(self):
        msg = Message(user_id="test", text="hello there", timestamp=123)
        agent, reply = self.router.handle(msg)
        assert agent == "bart"

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


class TestAgentPrefixParsing:
    """Test that agent prefixes are correctly stripped."""
    
    def setup_method(self):
        self.router = Router(history=MessageHistory())
    
    def test_jb_with_colon(self):
        msg = Message(user_id="test", text="jb: what do you think", timestamp=123)
        agent, reply = self.router.handle(msg)
        assert agent == "jb"
    
    def test_jb_with_comma(self):
        msg = Message(user_id="test", text="jb, what do you think", timestamp=123)
        agent, reply = self.router.handle(msg)
        assert agent == "jb"
    
    def test_bernie_with_space_only(self):
        msg = Message(user_id="test", text="bernie tell me something", timestamp=123)
        agent, reply = self.router.handle(msg)
        assert agent == "bernie"
    
    def test_just_agent_name_no_message(self):
        msg = Message(user_id="test", text="jb", timestamp=123)
        agent, reply = self.router.handle(msg)
        assert agent == "jb"


class TestMutedAgentRouting:
    """Test that muted agents route to Bart instead."""
    
    def setup_method(self):
        self.router = Router(history=MessageHistory())
    
    def test_muted_bernie_routes_to_bart(self):
        self.router.mute_agent("bernie")
        msg = Message(user_id="test", text="bernie: hello", timestamp=123)
        agent, reply = self.router.handle(msg)
        assert agent == "bart"
    
    def test_muted_jb_routes_to_bart(self):
        self.router.mute_agent("jb")
        msg = Message(user_id="test", text="jb: hello", timestamp=123)
        agent, reply = self.router.handle(msg)
        assert agent == "bart"
    
    def test_unmuted_agent_routes_normally(self):
        self.router.mute_agent("bernie")
        self.router.unmute_agent("bernie")
        msg = Message(user_id="test", text="bernie: hello", timestamp=123)
        agent, reply = self.router.handle(msg)
        assert agent == "bernie"