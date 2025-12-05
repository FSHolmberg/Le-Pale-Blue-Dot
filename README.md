# Le Pale Blue Dot (LPBD)

A philosophy-grounded multi-agent conversational AI system set in a noir bar in Calais, where six AI agents embody distinct philosophical perspectives and cognitive functions.

[![PyPI version](https://badge.fury.io/py/lpbd.svg)](https://badge.fury.io/py/lpbd)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install lpbd
```

Or install from source:

```bash
git clone https://github.com/FSHolmberg/Le-Pale-Blue-Dot.git
cd Le-Pale-Blue-Dot
pip install -e .
```

## Quick Start

```python
from src.router import Router
from src.schemas.message import Message
from time import time

# Set your Anthropic API key
# export ANTHROPIC_API_KEY="your-key-here"

# Initialize router
router = Router()

# Send a message
msg = Message(
    user_id="user1",
    text="bart, what's your take on failure?",
    timestamp=time()
)
agent, reply = router.handle(msg)

print(f"{agent}: {reply}")
```

## The Agents

Each agent represents a distinct philosophical perspective:

**Bart** (Bartender) - Probing conversationalist inspired by Nassim Taleb's antifragility. Asks uncomfortable questions that reveal hidden assumptions.

**Bernie** (Optimist) - Affirms the present without false hope, drawing from Camus's philosophy. Shares historical anecdotes of resilience.

**JB** (Language Critic) - Demands linguistic precision. Inspired by Camus's "The Fall" - treats language as moral responsibility.

**Blanca** (Moderator) - Tactical referee managing conversation flow. Named after chess master Capablanca - values structure over content.

**Hermes** (Ethical Oversight) - Crisis intervention specialist. Stoic ethics with practical resources. Automatically triggered by crisis keywords.

**Bukowski** (Ledger) - Mechanical archivist logging conversation states. Named after Charles Bukowski - unadorned truth-telling.

## Usage

### Direct agent routing

```
[message]                 # Talk to Bart (default)
bernie: [message]         # Talk to Bernie  
jb: [message]             # Talk to JB
hermes: [message]         # Talk to Hermes
blanca: [message]         # Talk to Hermes
```

### Bukowski commands

```
bukowski: note            # Log current conversation
bukowski: show last       # Display last entry
bukowski: delete last     # Remove last entry
```

### System commands

```
mute bernie               # Silence Bernie
unmute bernie             # Restore Bernie
```

Note: Bart, Blanca, and Hermes cannot be muted (essential functions).

### Crisis detection

Messages containing self-harm or violence keywords automatically route to Hermes.

## Current Status

**Version 0.1.0** - Core implementation complete

- 6 agents fully implemented with distinct personalities
- Crisis detection and ethical routing
- Mute/unmute functionality
- Message history persistence
- Bukowski ledger system
- 102 tests passing (97 behavioral + 5 property-based)

## Architecture

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
Agent Response (Claude API)
    ↓
History + Ledger Logging
```

## Development

```bash
# Clone and setup
git clone https://github.com/FSHolmberg/Le-Pale-Blue-Dot.git
cd Le-Pale-Blue-Dot
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest src/tests/ -v

# Run property-based tests
pytest src/tests/test_properties.py -v

# Run specific agent tests
pytest src/tests/test_bart.py -v
```

## Project Structure

```
lpbd/
├── src/
│   ├── agents/          # Six philosophical AI agents
│   ├── config/          # YAML configuration and prompts
│   ├── tests/           # 102 behavioral and property tests
│   ├── router.py        # Main routing logic
│   ├── history.py       # Message persistence
│   └── main.py          # CLI entry point
├── pyproject.toml       # Package configuration
└── README.md
```

## Philosophy

LPBD explores philosophical concepts through conversational AI:

- **Antifragility** (Bart) - Systems that gain from disorder
- **Absurdism** (Bernie) - Affirmation without false hope  
- **Linguistic Ethics** (JB) - Language as moral responsibility
- **Tactical Clarity** (Blanca) - Structure enables freedom
- **Stoic Intervention** (Hermes) - Practical ethics in crisis
- **Unadorned Truth** (Bukowski) - Documentation without interpretation

## Technical Stack

- Python 3.10+
- Anthropic Claude API (Sonnet 4)
- Pydantic for data validation
- Pytest + Hypothesis for testing
- YAML configuration

## Roadmap

- Flask web interface
- Railway deployment
- Bukowski standalone desktop app
- Visual novel integration (Hugo Pratt/Sean Phillips aesthetic)
- Enhanced weather integration

## License

MIT License - see LICENSE file

## Author

Fredrik Holmberg  
Email: fredriksayedholmberg@gmail.com  
GitHub: [@FSHolmberg](https://github.com/FSHolmberg)