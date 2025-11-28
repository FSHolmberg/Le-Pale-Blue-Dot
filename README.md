# Le Pale Blue Dot (LPBD)

A multi-agent conversational system set in a noir bar. Each agent represents a 
distinct cognitive function: clarity (Bart), safety (Blanca), language (JB), 
warmth (Bernie), ethics (Hermes), and memory (Bukowski).

---

## Status (Week 2)

**Working:**
- Bart (bartender, life advice via power-law thinking)
- Bernie (optimist, tells positive historical stories)
- JB (language critic, triggered manually)
- Blanca (safety, moderates caps/abuse)
- Bukowski (ledger, logs user notes)

**In Progress:**
- Hermes (ethical override)
- Agent auto-triggering (JB, Hermes)
- Mute/unmute toggles
- Pre-router safety scan

**Tests:** 23 passing

---

## Quick Start

### Install dependencies:
```bash
pip install anthropic pyyaml pytest
```

### Set API key:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### Run interactive terminal:
```bash
python send.py
```

### Test agents:
```bash
pytest -q
```

---

## Architecture
```
User message
    ↓
Router (routes based on prefix or content)
    ↓
Agent (Bart, Bernie, JB, Blanca, Bukowski, Hermes)
    ↓
LLMClient (Claude API wrapper)
    ↓
Response logged + returned
```

**Agents:**
- **Bart:** Default. Probes for clarity, suggests antifragile paths.
- **Bernie:** Prefix `bernie:`. Tells warm historical stories.
- **JB:** Triggered by `jb`. Critiques language quality.
- **Blanca:** Triggered by CAPS. Moderates behavior.
- **Bukowski:** Prefix `bukowski:`. Logs and retrieves notes.
- **Hermes:** (Coming) Ethical override for sensitive topics.

**Routing:**
- CAPS → Blanca
- `jb` → JB
- `bernie: ...` → Bernie
- `bukowski: ...` → Bukowski
- Everything else → Bart

---

## Project Structure
```
lpbd/
├── src/
│   ├── agents/
│   │   ├── bart.py          # Bartender (power-law probing)
│   │   ├── bernie.py        # Optimist (historical stories)
│   │   ├── jb.py            # Language critic
│   │   ├── blanca.py        # Safety/moderation
│   │   ├── bukowski.py      # Ledger commands
│   │   ├── bukowski_ledger.py  # Memory storage
│   │   ├── hermes.py        # Ethical interjector (stub)
│   │   └── llm_client.py    # Claude API wrapper
│   ├── config/
│   │   ├── loader.py        # YAML config loader
│   │   └── prompts.yaml     # Agent system prompts
│   ├── schemas/
│   │   └── message.py       # Pydantic message schema
│   └── tests/               # Pytest suite
├── router.py                # Message routing logic
├── history.py               # Conversation history
├── send.py                  # Interactive terminal interface
└── README.md
```

---

## Philosophy

LPBD is grounded in absurdist philosophy (Camus) and antifragility (Taleb). 

**Core principles:**
- Life follows power laws, not normal distributions
- Most attempts fail; rare attempts yield massive returns
- The bar is a place to stop lying and start building something real
- Agents probe for signal, not comfort

---

## Development Roadmap

**Phase 1 (Now → March 2026):**
- Week 1: Bart + Claude API integration
- Week 2: Bernie + JB + interactive send.py
- Week 3-4: Hermes, agent auto-triggering, safety layer
- Deliverable: 5 agents working, 50+ tests, v0.1 tag

**Phase 2 (April → Sept 2026):**
- FastAPI deployment
- Comprehensive testing
- Holmberg Grid (memory tool)
- Decency Digest (Bernie's archive)
- Deliverable: Production-ready v1.0

**Phase 3 (Oct 2026+):**
- UI (noir graphic novel aesthetic)
- CI/CD pipeline
- Monitoring & observability

---

## Contributing

This is a solo learning project. Not accepting PRs yet.

---

## License

Proprietary. Not open source (yet).