# Le Pale Blue Dot (LPBD)

A philosophy-grounded multi-agent conversational AI system set in a noir bar in Calais, where five AI agents embody distinct philosophical perspectives and cognitive functions.

[![PyPI version](https://badge.fury.io/py/lpbd.svg)](https://badge.fury.io/py/lpbd)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

LPBD is a conversational system where users interact with AI agents in a fictional bar on the northern French coast. Each agent has a distinct personality grounded in philosophical frameworks, creating conversations that challenge assumptions and explore ideas through multiple perspectives.

**Current Status**: Working prototype with functional frontend. Placeholder UI and active development toward soft opening to test audience.

## Quick Start

### Web Interface (Recommended)
```bash
# Clone and setup
git clone https://github.com/FSHolmberg/Le-Pale-Blue-Dot.git
cd Le-Pale-Blue-Dot
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"

# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Start the server
make run

# Open browser to http://localhost:8000
```

### Python API
```python
from src.router import Router
from src.schemas.message import Message
from time import time

router = Router()

msg = Message(
    user_id="user1",
    text="bart, what's your take on failure?",
    timestamp=time()
)
agent, reply = router.handle(msg)

print(f"{agent}: {reply}")
```

## The Bar

**Le Pale Blue Dot** - A 24/7 noir bar in Calais (opened November 1913, closes only on leap day). The bar features live weather from the English Channel, eclectic music (Afrobeat to The Young Gods), and five distinct voices.

## The Agents

**Bart** (Bartender) - Welsh Traveller, pushing 50. Probing conversationalist who challenges assumptions and suggests bold moves. Inspired by antifragility concepts and absurdist lucidity.

**Bernie** (Optimist) - Affirms the present without false hope. Shares historical anecdotes of human decency and resilience. Knows the bar's history.

**JB** (Language Critic) - Demands linguistic precision. Treats language as moral responsibility. A bit annoying, as language critics tend to be.

**Blanca** (Moderator/Bouncer) - Tactical referee managing conversation flow and boundaries. Values structure and knows when to intervene.

**Hermes** (Ethical Oversight) - Crisis intervention specialist. Automatically triggered by crisis keywords. Handles ethical dilemmas with practical resources.

~~**Bukowski** (Ledger)~~ - Mechanical archivist. *(Currently disabled - standalone desktop app in development)*

## Features

### Current (v0.1.0+)

- Five fully implemented agents with distinct personalities
- FastAPI backend with PostgreSQL session management
- Placeholder web interface (graphic novel aesthetic)
- Agent selection routing (click agent → direct message)
- Spatial speech bubble positioning
- Live Calais weather integration
- Crisis detection and automatic routing to Hermes
- Message history and persistence
- Modular YAML-based prompt system
- 102 passing tests (behavioral + property-based)

### In Development

- Conversation history (agents can reference previous exchanges)
- Response verbosity tuning
- Visual polish and production assets
- Bar lore and agent backstories
- Bukowski standalone desktop app
- Production deployment (Railway)

## Usage

### Web Interface

Click an agent's avatar to select them, then type your message. The agent will respond with a speech bubble positioned near them in the bar scene.

**Default**: Messages without agent selection go to Bart

### CLI/API
```python
# Direct routing
"[message]"              # → Bart (default)
"bernie: [message]"      # → Bernie  
"jb: [message]"          # → JB
"hermes: [message]"      # → Hermes
"blanca: [message]"      # → Blanca
```

### System Commands
```python
"mute bernie"            # Silence Bernie
"unmute bernie"          # Restore Bernie
```

Note: Bart, Blanca, and Hermes cannot be muted (essential functions).

### Crisis Detection

Messages containing self-harm or violence keywords automatically route to Hermes.

## Architecture

### Message Flow
```
User Input
    ↓
Pre-Router Scan (caps, empty messages) → Blanca
    ↓
Crisis Detection → Hermes (if triggered)
    ↓
Agent Prefix Parsing (bart:, bernie:, etc.)
    ↓
Mute Check (skip if muted)
    ↓
Agent Response (Claude Sonnet 4 via Anthropic API)
    ↓
History + Database Logging
```

### Tech Stack

**Backend**:
- Python 3.10+
- FastAPI for web API
- PostgreSQL for session persistence
- Anthropic Claude API (Sonnet 4)
- Pydantic for validation
- Pytest + Hypothesis for testing

**Frontend** (Placeholder):
- Vanilla JavaScript
- CSS positioning for spatial UI
- Graphic novel aesthetic (noir/dark turquoise palette)

## Project Structure
```
lpbd/
├── src/
│   ├── agents/              # Five philosophical AI agents
│   ├── config/
│   │   ├── prompts/         # Modular agent-specific YAML configs
│   │   └── loader.py        # Config management
│   ├── tests/               # 102 behavioral and property tests
│   ├── api.py               # FastAPI endpoints
│   ├── router.py            # Main routing logic
│   ├── history.py           # Message persistence
│   ├── calais_weather.py    # Live weather integration
│   └── main.py              # CLI entry point
├── frontend/                # Placeholder web interface
├── pyproject.toml           # Package configuration
└── README.md
```

## Development
```bash
# Setup
git clone https://github.com/FSHolmberg/Le-Pale-Blue-Dot.git
cd Le-Pale-Blue-Dot
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest src/tests/ -v

# Run server
make run

# Run specific agent tests
pytest src/tests/test_bart.py -v
```

## Philosophy

LPBD explores philosophical concepts through conversational AI:

- **Antifragility & Absurdism** (Bart) - Bold action in face of uncertainty
- **Historical Optimism** (Bernie) - Affirmation grounded in human decency  
- **Linguistic Ethics** (JB) - Precision as moral responsibility
- **Tactical Boundaries** (Blanca) - Structure enables meaningful exchange
- **Practical Ethics** (Hermes) - Intervention when stakes are real

The system rejects AI as productivity optimization—instead, it explores AI as a tool for creative provocation and philosophical inquiry.

## Design Principles

- **Grounded in place**: Real weather, specific location, physical space
- **Philosophically coherent**: Agents behave consistently with their frameworks
- **Anti-sycophant**: No corporate AI politeness, no optimization for comfort
- **Portfolio over product**: Demonstrates thoughtful AI design, not startup hustle

## License

MIT License - see LICENSE file

## Author

Fredrik Holmberg 
Email: fredriksayedholmberg@gmail.com  
GitHub: [@FSHolmberg](https://github.com/FSHolmberg)