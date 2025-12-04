# Le Pale Blue Dot (LPBD)

A philosophy-grounded multi-agent conversational system set in a noir bar in in a northern port town, where each character represents distinct cognitive functions.

## Current Status

**Phase 1: Core Implementation (In Progress)**

- Router with mute/unmute functionality
- Crisis detection and ethical routing
- Pre-router scanning for tone violations
- Message history tracking
- 5 agents fully implemented and tested

**Agents Implemented:**
- **Bart** - Bartender (probing, Taleb's antifragility) - 3/3 tests passing
- **Bernie** - Optimist (positive historical stories, Camus's affirmation) - 3/3 tests passing
- **JB** - Language critic (precision, irritated clarity) - 3/3 tests passing
- **Hermes** - Ethical oversight (crisis intervention, resources) - 5/5 tests passing
- **Bukowski** - Ledger/logging system (mechanical archivist) - 15/15 tests passing
- **Blanca** - Moderator (tactical referee, conversation flow) - 11/11 tests passing

**Total: 40/40 behavioral tests passing**

## Philosophy

Each agent embodies specific philosophical concepts:

- **Bart**: Nassim Taleb's antifragility - systems that gain from disorder
- **Bernie**: Camus's affirmation without hope - present-focused positivity
- **JB**: Linguistic precision inspired by "The Fall" - language as moral responsibility
- **Blanca**: Capablanca's tactical clarity - structure over content
- **Hermes**: Stoic ethics with practical intervention
- **Bukowski**: Charles Bukowski's gritty realism - unadorned truth

## Architecture

```
User Input
    ↓
Blanca Pre-Router Scan (CAPS, empty messages)
    ↓
Crisis Detection (routes to Hermes if triggered)
    ↓
Router (parses agent prefix: "bart:", "bernie:", etc.)
    ↓
Agent Response (via Claude API)
    ↓
History Logging
```

## Installation

```bash
# Clone repository
git clone [your-repo-url]
cd lpbd

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up API key
export ANTHROPIC_API_KEY="your-key-here"
```

## Usage

```bash
# Run LPBD
python3 src/main.py

# Run tests
pytest src/tests/ -v

# Run specific agent tests
pytest src/tests/test_bart.py -v
pytest src/tests/test_bukowski.py -v
pytest src/tests/test_blanca.py -v

# Clear LLM cache (after prompt changes)
make cache

# Clean Python cache
make clean

# Run chat via send.py
make run
```

## Commands

**Agent routing:**
```
bart: [your message]      # Talk to Bart (default if no prefix)
bernie: [your message]    # Talk to Bernie
jb: [your message]        # Talk to JB
blanca: [your message]    # Talk to Blanca
bukowski: note            # Log current conversation state
bukowski: show last       # Show last logged entry
bukowski: delete last     # Remove last entry
```

**System commands:**
```
mute [agent]              # Silence an agent
unmute [agent]            # Restore an agent
```

**Crisis triggers:**
Any mention of self-harm, suicide, or violence automatically routes to Hermes.

## Project Structure

```
lpbd/
├── src/
│   ├── agents/
│   │   ├── bart.py              # Bartender agent
│   │   ├── bernie.py            # Optimist agent
│   │   ├── jb.py                # Language critic agent
│   │   ├── hermes.py            # Ethical oversight agent
│   │   ├── bukowski.py          # Ledger system
│   │   ├── bukowski_ledger.py   # Ledger data structure
│   │   └── blanca.py            # Moderator agent
│   ├── config/
│   │   ├── loader.py            # Configuration loader
│   │   └── prompts.yaml         # Agent system prompts
│   ├── tests/
│   │   ├── test_bart.py
│   │   ├── test_bernie.py
│   │   ├── test_jb.py
│   │   ├── test_hermes.py
│   │   ├── test_bukowski.py
│   │   └── test_blanca.py
│   ├── history.py               # Message history tracking
│   ├── llm_client.py            # Claude API wrapper
│   ├── message.py               # Message data structure
│   ├── router.py                # Main routing logic
│   ├── logger_setup.py          # Logging configuration
│   └── main.py                  # Entry point
├── Makefile                     # Build commands
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Development Principles

1. **Philosophy-driven design** - Each agent has clear conceptual grounding
2. **Behavioral testing** - Verify personality, not just functionality
3. **Modularity** - Components can be extracted (see Bukowski extraction)
4. **Git discipline** - Commit after each working feature

## Testing Philosophy

Tests validate **behavior** not just function:
- Agents maintain consistent personality (tone, brevity, style)
- No meta-commentary ("as an AI", "language model")
- No stage directions (asterisks, action brackets)
- Appropriate emotional detachment/warmth per agent

## Technical Stack

- **Python 3.14**
- **Anthropic Claude API** (claude-3-5-sonnet-20241022)
- **pytest** for testing
- **YAML** for configuration

## Contributing

This is a personal learning/portfolio project. Not currently accepting contributions, but feedback and suggestions are welcome.

## License

[Add license]

## Contact

fsholmberg@gmail.com
