# LPBD Architecture Documentation

## Database Schema

### users
- `id` (UUID, primary key)
- `anonymous_id` (UUID, unique) - browser session identifier
- `created_at` (timestamp)
- `invite_code` (string, nullable) - soft opening access control

### sessions
- `id` (UUID, primary key)
- `user_id` (UUID, foreign key → users.id)
- `started_at` (timestamp)
- `ended_at` (timestamp, nullable)
- `status` (enum: active/warning_15min/kicked/ended)
- `crisis_flag_date` (date, nullable) - set by Hermes, 7-day decay
- `weather` (JSON, nullable) - snapshot at session start for Bart's reference
- `message_count` (integer) - tracks toward session limit

### messages
- `id` (UUID, primary key)
- `session_id` (UUID, foreign key → sessions.id)
- `agent` (string) - which agent spoke (or "user")
- `content` (text)
- `timestamp` (timestamp)
- `is_user_message` (boolean)

## Session Lifecycle

**Active session:**
- User sends message → timer resets
- After 15 min user inactivity → Bart asks if still there, status = warning_15min
- After 5 min more (20 min total) → Blanca kicks out, status = kicked, ended_at set

**Ended session:**
- Status changed to "ended", ended_at timestamp recorded
- User outside bar, must knock (start new session) to continue
- Previous session persists for Bart's memory

**Session termination triggers:**
- 20 min total inactivity
- User reaches message limit (TBD: 20-30 messages?)
- "Last call" warning at limit-5 messages, then forced graceful end

## Bart's Memory System

**Cold storage (historical):**
- Last 4 completed sessions
- Each stored as: first 3 messages + last 10 messages (compressed)
- When current session ends → compress to (first 3 + last 10) → push to cold storage → drop oldest if >4 sessions

**Hot storage (current session):**
- All messages from active session
- Sliced to (first 3 + last 10) when building Bart's context
- Not compressed until session ends

**Context construction for Bart:**
- System prompt (3000 chars / ~600-750 tokens)
- Cold storage: 4 previous sessions × 13 messages each
- Hot storage: current session (first 3 + last 10)
- Total: ~52 historical + ~13 current = ~65 messages in Bart's context

**Weather integration:**
- Session weather snapshot stored at session start
- Bart can reference: "You came in on a rainy Tuesday mumbling about Senegal"

## Crisis Handling

**Detection:**
- Hermes monitors for crisis indicators (self-harm, acute distress)
- Router (Haiku LLM) can override user agent selection → force Hermes

**Response flow:**
1. Crisis detected → Hermes responds (intercepting other agent)
2. `crisis_flag_date` set to today in sessions table
3. Blanca notified for future messages (system prompt update)
4. Flag decays after 7 days (auto-expires)

**Behavioral changes during flag period:**
- Blanca: gentler tone, early check-in ("How are you doing today?")
- Bart: slightly more careful with dark humor (prompt adjustment)
- User sees: Blanca mentions support available via Hermes

**False positive mitigation:**
- Philosophical discussions (Camus, absurdism) should NOT trigger
- Context matters: router evaluates tone, not just keywords
- User can dismiss: continue conversation normally after Hermes check-in

## Frontend-Backend Contract

### Request: POST /message
```json
{
  "session_id": "uuid",
  "content": "user message text (max 500 chars)",
  "selected_agent": "bernie" // optional, if user clicked agent portrait
}
```

### Response: Agent message
```json
{
  "agent": "bernie", // actual responding agent (may differ from selected)
  "message": "agent response text",
  "timestamp": "ISO datetime",
  "agents_available": ["bart", "bernie", "jb"],
  "agents_muted": ["bukowski"],
  "session_status": "active" | "warning_15min" | "kicked",
  "message_count": 12, // current message count in session
  "message_limit": 30 // session limit
}
```

### Other endpoints
- `POST /session/start` → create session, return session_id + initial state
- `GET /session/{id}/status` → check timeout status without sending message
- `POST /session/end` → manual session termination (user leaves properly)

## Cost Controls

**Character limits:**
- User messages: 500 characters max (frontend + backend validation)
- Agent responses: 200 tokens max (API max_tokens parameter)
- Enforced via textarea maxlength + character counter on frontend

**Message limits per session:**
- Target: 20-30 messages total per session
- "Last call" warning at limit-5 messages
- Graceful session end when limit reached

**Rate limiting:**
- Max sessions per user per day: 3-5 (tracked by anonymous_id)
- Prevents cost runaway from single user

**Prompt caching (critical for cost):**
- Cache agent system prompts using Anthropic's cache_control
- Cache Bart's cold storage (historical memory)
- 90% discount on cached tokens after first message
- Cache lifetime: 5 minutes (reused within same session)
- Estimated savings: $9-18 → under $2 per 1000 messages

**Cost estimate (1000 user messages with controls):**
- With caching + limits: $8-15 total
- Without caching: $15-30 total
- Prompt caching is highest-impact optimization

## Router Design

**Hybrid LLM + user selection:**
- User can click agent portrait → suggestion sent to router
- Router (Haiku 4) evaluates: user message + selected agent + context
- Router decides: confirm selection OR override with better match
- Override scenarios: crisis (→ Hermes), moderation (→ Blanca), topic mismatch

**Router LLM call:**
- Model: Haiku 4 (fast, cheap)
- Input: user message, selected_agent, recent context (last 3 messages)
- Output: agent_name + optional reasoning
- Cost: ~$0.0001-0.0003 per routing decision

**Routing priority:**
1. Crisis detection → Hermes (always)
2. Moderation needed → Blanca (always)
3. User selection → honored if reasonable
4. No selection → router chooses based on message content

**Fallback:**
- Router fails or times out → default to Bart
- Bart is always safe fallback (bartender handles everything)

## Notes & Open Questions

**Soft opening access control:**
- Invite codes: generate 10 unique codes, one per friend
- User enters code on first visit → stored with anonymous_id
- Can disable specific code if needed
- No passwords, no email, no proper auth

**Agent moods:**
- Deferred post-soft-opening
- Not in database schema for now
- Can add `agent_moods` JSON column to sessions later

**Message limit specifics:**
- TBD: exact limit (20? 30?)
- TBD: "last call" timing (limit-5? limit-3?)
- Decide during testing based on conversation flow

**Logging vs Database:**
- PostgreSQL: stores messages/sessions for agent memory + functionality
- JSON logs: application events, errors, debugging (separate concern)
- Logs go to Railway dashboard, database stores conversation data