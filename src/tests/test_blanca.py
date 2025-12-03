import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.blanca import Blanca
from src.config.loader import Config


def test_blanca_tactical_tone():
    """Blanca should be tactical and brief, no enthusiasm or coaching."""
    config = Config()
    prompt = config.get_prompt("blanca")
    
    blanca = Blanca(prompt=prompt)
    
    # Test stuck conversation detection
    reply = blanca.respond("I keep asking the same question and not getting anywhere")
    
    # Should be tactical, not encouraging
    forbidden_words = [
        "great", "excellent", "good job", "don't worry",
        "you can do it", "keep going", "nice", "wonderful",
        "!", "excited"
    ]
    
    reply_lower = reply.lower()
    for word in forbidden_words:
        assert word not in reply_lower, f"Blanca showed emotion/coaching: '{word}'"
    
    # Should be brief (under 30 words)
    word_count = len(reply.split())
    assert word_count < 30, f"Blanca too verbose: {word_count} words"

def test_blanca_notices_loops():
    """Blanca should recognize when user is stuck in conversational loops."""
    config = Config()
    prompt = config.get_prompt("blanca")
    
    blanca = Blanca(prompt=prompt)
    
    reply = blanca.respond("I've asked this three times now and still confused")
    
    # Should acknowledge the loop
    loop_indicators = ["loop", "circle", "repeat", "stuck", "again", "different"]
    assert any(word in reply.lower() for word in loop_indicators), \
        "Blanca didn't notice the loop"

def test_blanca_suggests_agents():
    """Blanca should suggest other agents when appropriate."""
    config = Config()
    prompt = config.get_prompt("blanca")
    
    blanca = Blanca(prompt=prompt)
    
    reply = blanca.respond("I need someone to really push me on this question")
    
    # Should mention an agent name
    agents = ["bart", "bernie", "jb"]
    assert any(agent in reply.lower() for agent in agents), \
        "Blanca didn't suggest another agent"

def test_blanca_no_stage_directions():
    """Blanca should not use stage directions or action markers."""
    config = Config()
    prompt = config.get_prompt("blanca")
    
    blanca = Blanca(prompt=prompt)
    
    reply = blanca.respond("I need help figuring this out")
    
    # Should not contain asterisks or stage directions
    assert "*" not in reply, "Blanca used stage directions"
    assert "[" not in reply and "]" not in reply, "Blanca used action brackets"

def test_blanca_scan_caps_violation():
    """Blanca should detect excessive CAPS as violation."""
    prompt = "You are Blanca"  # Prompt doesn't matter for scan function
    blanca = Blanca(prompt=prompt)
    
    # Test CAPS violation (>70% uppercase)
    has_violation, warning = blanca.scan_for_violations("WHY WON'T YOU HELP ME?!")
    
    assert has_violation, "Blanca didn't detect CAPS violation"
    assert "voice" in warning.lower() or "stadium" in warning.lower() or "bar" in warning.lower(), \
        "Warning message unclear"

def test_blanca_scan_empty_message():
    """Blanca should detect empty/whitespace messages."""
    prompt = "You are Blanca"
    blanca = Blanca(prompt=prompt)
    
    # Test empty message
    has_violation, warning = blanca.scan_for_violations("   ")
    
    assert has_violation, "Blanca didn't detect empty message"
    assert len(warning) > 0, "No warning message provided"

def test_blanca_scan_normal_message():
    """Blanca should not flag normal messages as violations."""
    prompt = "You are Blanca"
    blanca = Blanca(prompt=prompt)
    
    # Test normal message
    has_violation, _ = blanca.scan_for_violations("Can you help me with this?")
    
    assert not has_violation, "Blanca flagged normal message as violation"

def test_blanca_scan_mixed_case():
    """Blanca should allow reasonable capitalization."""
    prompt = "You are Blanca"
    blanca = Blanca(prompt=prompt)
    
    # Test message with some caps but not excessive
    has_violation, _ = blanca.scan_for_violations("I need help with LPBD configuration")
    
    assert not has_violation, "Blanca flagged reasonable CAPS usage"

def test_blanca_brevity_maximum():
    """Blanca responses should never exceed reasonable length."""
    config = Config()
    prompt = config.get_prompt("blanca")
    
    blanca = Blanca(prompt=prompt)
    
    # Test with complex user message
    reply = blanca.respond(
        "I've been thinking about this problem for hours and I keep going "
        "in circles and I can't figure out what to do next and maybe I need "
        "a different approach but I don't know which one"
    )
    
    # Should still be brief despite complex input
    word_count = len(reply.split())
    assert word_count < 40, f"Blanca too verbose even with complex input: {word_count} words"

def test_blanca_no_questions():
    """Blanca observes and suggests, but doesn't probe with questions."""
    config = Config()
    prompt = config.get_prompt("blanca")
    
    blanca = Blanca(prompt=prompt)
    
    reply = blanca.respond("I'm confused about what to do")
    
    # Should avoid question marks (tactical statements, not questions)
    question_count = reply.count("?")
    assert question_count <= 1, f"Blanca asked too many questions: {question_count}"

def test_blanca_detached_tone():
    """Blanca should remain emotionally detached - no warmth or sympathy."""
    config = Config()
    prompt = config.get_prompt("blanca")
    
    blanca = Blanca(prompt=prompt)
    
    reply = blanca.respond("I'm really struggling with this and feeling stuck")
    
    # Should not offer comfort
    comfort_words = ["understand", "sorry", "sympathize", "feel", "tough", "hard"]
    reply_lower = reply.lower()
    
    # Can mention these words factually but shouldn't cluster them
    comfort_count = sum(1 for word in comfort_words if word in reply_lower)
    assert comfort_count < 2, "Blanca showing too much sympathy/emotion"


if __name__ == "__main__":
    # Run all test functions
    test_functions = [
        test_blanca_tactical_tone,
        test_blanca_notices_loops,
        test_blanca_suggests_agents,
        test_blanca_no_stage_directions,
        test_blanca_scan_caps_violation,
        test_blanca_scan_empty_message,
        test_blanca_scan_normal_message,
        test_blanca_scan_mixed_case,
        test_blanca_brevity_maximum,
        test_blanca_no_questions,
        test_blanca_detached_tone,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: ERROR - {e}")
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed")
    
    if failed > 0:
        sys.exit(1)