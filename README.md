
# Le-Pale-Blue-Dot
A multi-agent, stateful LLM ecosystem for rhetorical analysis and ethical filtering.
=======


# Le Pale Blue Dot (LPBD)

A small, single-room noir bar running inside a FastAPI app.
The user is in the bar speaking directly to staff and regulars.
Three (soon six) agents are overhearing everything:

- **Bart** – the main communicator; an unimpressed bartender giving life advice
- **Blanca** – the moderator; a bouncer who throws you out if you don't behave
- **JB** – the language critic, currently a dry stub

Behind the curtain it’s a testable, multi-agent routing engine.

---

## Overview

LPBD is a draft implementation of a character-based conversational system:

- FastAPI backend with a `/chat` endpoint
- Router that selects an agent based on message text
- Three (to be six) agents implemented as Python classes
- Pydantic schema for messages
- Minimal terminal chat client
- Pytest test suite (all green)

The world-building (bar, agents, rules) is defined in the LPBD logic doc; this repository is the first implementation pass.

---

## Project Structure

```text
lpbd/
  conftest.py          # Ensures src/ is importable in tests
  main.py              # FastAPI app and /chat route
  router.py            # Router class selecting agents

  src/
    __init__.py
    agents/
      __init__.py
      bart.py          # Bart agent (real logic)
      blanca.py        # Blanca agent (stub)
      jb.py            # JB agent (stub)
    config/
      __init__.py
      agents.py        # Placeholder config for future prompts (currently unused)
    schemas/
      __init__.py
      message.py       # Pydantic Message model
    tests/
      __init__.py
      test_bart.py     # Unit tests for Bart
      test_jb.py       # Router test for JB selection
      test_router.py   # Router behaviour tests

  send.py              # Terminal client posting to /chat
```   

---


## Installation

#pip install fastapi uvicorn requests pydantic pytest

## Running

uvicorn main:app --reload --port 8000
python3 send.py

---

...that's it for now. just getting started
