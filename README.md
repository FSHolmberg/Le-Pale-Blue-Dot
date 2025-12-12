# Le Pale Blue Dot (LPBD)

A philosophy-grounded multi-agent conversational AI system set in a noir bar in Calais, where five AI agents embody distinct philosophical perspectives and cognitive functions.

[![PyPI version](https://badge.fury.io/py/lpbd.svg)](https://badge.fury.io/py/lpbd)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

LPBD is a conversational system where users interact with AI agents in a fictional bar on the northern French coast. Each agent has a distinct personality grounded in philosophical frameworks, creating conversations that challenge assumptions and explore ideas through multiple perspectives.

**Current Status**: Working prototype with intelligent routing, conversation memory, and functional web interface (placeholder art). Active development toward soft opening (mid-January 2025).

## Quick Start

### Web Interface (Recommended)
```bash
# Clone and setup
git clone https://github.com/FSHolmberg/Le-Pale-Blue-Dot.git
cd Le-Pale-Blue-Dot
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"

# Setup database
psql -c "CREATE DATABASE lpbd_dev;"
python -c "from src.database.models import init_db; init_db()"

# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Start the server
uvicorn src.api:app --reload

# Open browser to http://localhost:8000
```

### Python API
```python
from src.router import Router
from src.schemas.message import Message

router = Router()

msg = Message(
    user_id="user1",
    text="I'm feeling down, any sunshine stories?",
    session_id="session123"
)
agent, reply = router.handle(msg)

print(f"{agent}: {reply}")
```

## The Bar

**Le Pale Blue Dot** - A 24/7 noir bar in Calais (opened November 1913, closes only on leap day). The bar features live weather from the English Channel, real tide data, eclectic music (Afrobeat to The Young Gods), and five distinct voices.

## The Agents

**Bart** (Bartender) - Welsh Traveller, pushing 50. Probing conversationalist who challenges assumptions and suggests bold moves. Default agent for general conversation.

**Bernie** (Optimist) - Warm regular who shares positive historical stories from the "Decency Digest." Offers gentle perspective and affirmation.

**JB** (Language Critic) - British language perfectionist. Eviscerates bad grammar and imprecise language with contemptuous precision.

**Blanca** (Moderator/Bouncer) - Tactical observer who sits by the entrance. Manages conversation flow and boundaries with clinical detachment.

**Hermes** (Crisis Counselor) - Quiet philosopher who handles ethical dilemmas and crisis intervention with practical resources.

~~**Bukowski** (Ledger)~~ - Mechanical archivist. *(Currently disabled - standalone desktop app in development)*

## Features

### Current (v0.2.0)

**Core System:**
- Five fully implemented agents with distinct personalities
- LLM-based routing with integrated crisis detection (single Haiku call)
- Conversation memory system (cold/hot storage architecture)
- Session-based onboarding flow with returning user recognition
- FastAPI backend with PostgreSQL for session management
- Web interface with Sean Phillips-inspired noir aesthetic

**Routing Intelligence:**
- Smart agent selection based on user intent with agent stickiness
- Integrated crisis detection (distinguishes philosophical discussion from genuine distress)
- Explicit handoffs: agents can say "Let me get [Agent]" to pass conversation
- Manual agent selection via portrait click or text prefix
- Handoff detection in router for seamless agent transitions

**Context Integration:**
- Live Calais weather and time (OpenWeatherMap API)
- Real tide data for Calais harbor
- Bar lore and character backstories injected into agent context
- Onboarding context flows from Blanca through to bar entry
- Session-based conversation archiving (first 3 + last 10 messages)

**Visual Design:**
- Graphic novel aesthetic (turquoise/orange noir palette)
- Comic book typography (uppercase, Special Elite font)
- Agent portraits with hover states and selection
- Speech bubbles positioned spatially near speakers (not fully aligned)
- Placeholder art (Sean Phillips style, pending commissioned work)

**Testing:**
- 102 passing tests (behavioral + property-based)
- Modular YAML-based prompt system
- Full test coverage for routing and memory systems

### In Development

- Response verbosity tuning (agents sometimes too verbose)
- Visual polish and production assets (commissioned noir artwork)
- Enhanced agent backstories and bar lore
- Bukowski standalone desktop app
- Production deployment (Railway)

## Usage

### Web Interface

The system intelligently routes your message to the most appropriate agent:

- **General conversation** → Bart
- **Feeling down, need encouragement** → Bernie  
- **Language/grammar help** → JB
- **Ethical questions** → Hermes
- **Crisis keywords** → Hermes (automatic)

You can also click an agent's avatar to speak with them directly, or type their name:
```
"bernie, got any sunshine stories?"
"jb, how do I write this better?"
```

**Agent Stickiness**: Once you're talking to an agent, the system keeps you with them unless you explicitly ask for someone else or the topic clearly changes.

### System Commands
```python
"mute bernie"            # Silence Bernie (Bernie and JB can be muted)
"unmute bernie"          # Restore Bernie
```

Note: Bart, Blanca, and Hermes cannot be muted (essential functions).

### Crisis Detection

Messages containing self-harm or violence keywords automatically route to Hermes, who provides crisis resources.

## Architecture

### Message Flow
```
User Input
    ↓
Pre-Router Scan (caps, empty messages) → Blanca
    ↓
Crisis Detection → Hermes (if triggered)
    ↓
LLM Router (Haiku 4.5) → Determines best agent based on:
    - Current agent (stickiness)
    - User intent
    - Topic expertise needed
    ↓
Memory Injection → Loads conversation history:
    - Cold storage: Last 4 sessions (3 first + 10 last messages each)
    - Hot storage: Current session (all messages)
    ↓
Agent Response (Claude Sonnet 4.5)
    ↓
Session Update → Store in PostgreSQL
```

### Tech Stack

**Backend**:
- Python 3.14
- FastAPI for web API
- PostgreSQL for session persistence & conversation memory
- SQLAlchemy ORM
- Anthropic Claude API (Sonnet 4.5 for agents, Haiku 4.5 for routing)
- Pydantic for validation
- Pytest + Hypothesis for testing

**Frontend**:
- Vanilla JavaScript
- CSS positioning for spatial UI
- Graphic novel aesthetic (noir/dark turquoise palette)
- Placeholder art (commissioned work in progress)

## Project Structure
```
lpbd/
├── src/
│   ├── agents/              # Five philosophical AI agents
│   ├── config/
│   │   ├── prompts/         # Modular agent-specific YAML configs
│   │   └── loader.py        # Config management
│   ├── database/
│   │   ├── models.py        # SQLAlchemy models (User, Session, Message, MessageArchive)
│   │   └── memory_manager.py # Cold/hot storage for conversation history
│   ├── tests/               # 102 behavioral and property tests
│   ├── api.py               # FastAPI endpoints
│   ├── router.py            # LLM-based routing with agent stickiness
│   ├── calais_weather.py    # Live weather integration
│   └── schemas/             # Pydantic models
├── frontend/                # Web interface
├── Makefile                 # Common commands (make sesh, make run)
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

# Setup database
psql -c "CREATE DATABASE lpbd_dev;"
python -c "from src.database.models import init_db; init_db()"

# Run tests
pytest src/tests/ -v

# Run server
uvicorn src.api:app --reload

# Debug: View last conversation
make sesh

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
- **Intelligent routing**: LLM decides which agent best serves the conversation
- **Conversation continuity**: Agents remember context, conversations feel natural
- **Anti-sycophant**: No corporate AI politeness, no optimization for comfort
- **Portfolio over product**: Demonstrates thoughtful AI design, not startup hustle

## Roadmap

**v0.2.0** (Current): LLM routing + conversation memory  
**v0.3.0** (Jan 2025): Visual polish + soft opening  
**v0.4.0** (Q1 2025): Bukowski standalone app  
**v1.0.0** (Q2 2025): Public launch + production deployment

## License

MIT License - see LICENSE file

## Author

Fredrik Holmberg  
Email: fredriksayedholmberg@gmail.com  
GitHub: [@FSHolmberg](https://github.com/FSHolmberg)