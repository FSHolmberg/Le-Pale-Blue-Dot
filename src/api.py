from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DBSession
from typing import Optional, List
from datetime import datetime, timezone
from src.router import Router
from src.calais_weather import get_calais_environment
from src.database.models import get_db, User, Session, Message as DBMessage
from src.config.loader import Config
from src.schemas.message import Message
from src.calais_weather import get_environment_for_agent

import uuid
import time
import secrets
import os
import anthropic

security = HTTPBasic()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

app = FastAPI(title="Le Pale Blue Dot API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify HTTP Basic Auth credentials"""
    correct_username = secrets.compare_digest(
        credentials.username, 
        os.getenv("LPBD_USERNAME", "lpbd_user")
    )
    correct_password = secrets.compare_digest(
        credentials.password,
        os.getenv("LPBD_PASSWORD", "changeme123")
    )
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# --- Request/Response Models ---

class SessionStartResponse(BaseModel):
    session_id: str
    weather: str
    available_agents: List[str]
    timestamp: str

class MessageRequest(BaseModel):
    session_id: str
    content: str = Field(..., min_length=1, max_length=500)
    selected_agent: Optional[str] = None

class MessageResponse(BaseModel):
    agent: str
    message: str
    timestamp: str
    agents_available: List[str]
    agents_muted: List[str]
    session_status: str
    message_count: int
    message_limit: int

class OnboardRequest(BaseModel):
    anonymous_id: str
    message: Optional[str] = None  # None for initial greeting, then user responses

class OnboardResponse(BaseModel):
    message: str
    approved: bool
    continue_onboarding: bool  # True if more questions needed


# --- Endpoints ---

@app.post("/session/start")
async def start_session(
    request: dict, 
    username: str = Depends(verify_credentials),
    db: DBSession = Depends(get_db)):

    anonymous_id = request.get('anonymous_id')
    
    # Get or create user
    user = db.query(User).filter(User.anonymous_id == anonymous_id).first()
    if not user:
        user = User(anonymous_id=anonymous_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Get weather ONCE at session start
    from src.calais_weather import get_environment_for_agent
    weather = get_environment_for_agent()
    
    # Create session WITH weather
    session = Session(
        user_id=user.id,
        started_at=datetime.now(timezone.utc),
        status="active",
        weather=weather,  # Store in session for entire session
        message_count=0
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return {"session_id": session.id, "status": "active"}

@app.post("/message", response_model=MessageResponse)
async def send_message(
    request: MessageRequest,
    username: str = Depends(verify_credentials),
    db: DBSession = Depends(get_db)):

    # Get session from database
    session = db.query(Session).filter(Session.id == request.session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check session status
    if session.status in ["kicked", "ended"]:
        raise HTTPException(
            status_code=403,
            detail=f"Session has {session.status}. Start a new session.")
    
    # Check message limit
    if session.message_count >= 30:
        session.status = "ended"
        db.commit()
        raise HTTPException(status_code=429, detail="Message limit reached.")
    
    # === HANDLE ENTRANCE GREETING ===
    if request.content == "::USER_ENTERED_BAR::":
        # Initialize Router WITH WEATHER
        router = Router(weather_context=session.weather)
        
        # Build Message for Router (empty text, just context)
        msg = Message(
            user_id=session.user_id,
            text="User just walked in",
            session_id=request.session_id
        )
        
        # Get Bart's greeting with full context
        agent_response = router.execute_agent('bart', msg, db_session=db)
        
        # Store only Bart's greeting (not the system message)
        agent_message = DBMessage(
            session_id=session.id,
            agent='bart',
            content=agent_response,
            timestamp=datetime.now(timezone.utc),
            is_user_message=0
        )
        db.add(agent_message)
        db.commit()
        
        return MessageResponse(
            agent='bart',
            message=agent_response,
            timestamp=datetime.now(timezone.utc).isoformat(),
            agents_available=["bart", "bernie", "jb", "blanca", "hermes"],
            agents_muted=[],
            session_status=session.status,
            message_count=session.message_count,
            message_limit=30
        )
    
    # Last call warning
    warning = None
    if session.message_count == 25:
        warning = "Last call! Five messages remaining."
    
    # Store user message in database
    user_message = DBMessage(
        session_id=session.id,
        agent="user",
        content=request.content,
        timestamp=datetime.now(timezone.utc),
        is_user_message=1
    )
    db.add(user_message)
    session.message_count += 1
    db.commit()
    
    # Initialize Router WITH WEATHER
    router = Router(weather_context=session.weather)
    
    # Build Message for Router
    msg = Message(
        user_id=session.user_id,
        text=request.content,
        session_id=request.session_id
    )

    # ROUTING LOGIC (with handoff support)
    # Priority: 1. Pending handoff, 2. Manual selection, 3. Auto-routing
    if session.pending_handoff and not request.selected_agent:
        # Handoff takes priority
        agent_name = session.pending_handoff
        agent_response = router.execute_agent(session.pending_handoff, msg, db_session=db)
        # Clear the handoff
        session.pending_handoff = None
        db.commit()
    elif request.selected_agent:
        # Manual agent selection
        agent_name = request.selected_agent
        agent_response = router.execute_agent(request.selected_agent, msg, db_session=db)
    else:
        # Auto-routing - pass current agent for stickiness
        router.last_agent = session.current_agent  # Tell router who user is talking to
        agent_name, agent_response = router.handle(msg, db_session=db)
    
    # Update current agent in session (after all routing paths)
    session.current_agent = agent_name
    db.commit()
    
    # Check if agent said "Let me get [Agent]" for handoff
    if "let me get" in agent_response.lower():
        import re
        match = re.search(r'let me get (\w+)', agent_response.lower())
        if match:
            target_agent = match.group(1)
            if target_agent in ['bernie', 'jb', 'hermes', 'blanca']:
                session.pending_handoff = target_agent
                db.commit()
    
    # Add warning if needed
    if warning:
        agent_response = f"{warning}\n\n{agent_response}"
    
    # Store agent message in database
    agent_message = DBMessage(
        session_id=session.id,
        agent=agent_name,
        content=agent_response,
        timestamp=datetime.now(timezone.utc),
        is_user_message=0
    )
    db.add(agent_message)
    db.commit()
    
    return MessageResponse(
        agent=agent_name,
        message=agent_response,
        timestamp=datetime.now(timezone.utc).isoformat(),
        agents_available=["bart", "bernie", "jb", "blanca", "hermes"],
        agents_muted=list(router.muted_agents) if hasattr(router, 'muted_agents') else [],
        session_status=session.status,
        message_count=session.message_count,
        message_limit=30
    )

@app.post("/api/onboard")
async def onboard(request: OnboardRequest, db: Session = Depends(get_db)):
    """
    Onboarding:
    - Returning users: Quick greeting, let them in
    - New users: Age, name, pronouns, what brings them, been to similar places
    """
    
    # Get or create user
    user = db.query(User).filter_by(anonymous_id=request.anonymous_id).first()
    if not user:
        user = User(anonymous_id=request.anonymous_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Check if returning user (has completed sessions)
    completed_sessions = db.query(Session).filter_by(
        user_id=user.id,
        status="ended"
    ).count()
    
    is_returning = completed_sessions > 0
    
    # === RETURNING USER PATH ===
    if is_returning:
        if request.message is None:
            name = user.onboarding_context.get('name', 'friend') if user.onboarding_context else 'friend'
            return OnboardResponse(
                message=f"Back again, {name}? Go on in.",
                approved=True,
                continue_onboarding=False
            )
    
    # === NEW USER PATH ===
    # Get or initialize context - MAKE A COPY
    if user.onboarding_context is None:
        context = {'step': 'initial'}
    else:
        context = dict(user.onboarding_context)  # Make a copy!

    # FIRST VISIT - ask age (only if no message AND initial step)
    if request.message is None:
        if context.get('step') == 'initial':
            context['step'] = 'age'
            user.onboarding_context = context
            db.commit()
            return OnboardResponse(
                message="First time here? How old are you?",
                approved=False,
                continue_onboarding=True
            )
        elif context.get('step') == 'complete':
            # Returning user who already completed onboarding
            name = context.get('name', 'friend')
            return OnboardResponse(
                message=f"Back again, {name}? Go on in.",
                approved=True,
                continue_onboarding=False)
        elif context.get('step') == 'age':
            return OnboardResponse(
                message="How old are you?",
                approved=False,
                continue_onboarding=True
            )
        elif context.get('step') == 'name':
            return OnboardResponse(
                message="What should I call you?",
                approved=False,
                continue_onboarding=True
            )
        elif context.get('step') == 'pronouns':
            return OnboardResponse(
                message="Pronouns? Or skip.",
                approved=False,
                continue_onboarding=True
            )
        elif context.get('step') == 'motivation':
            return OnboardResponse(
                message="What brings you here?",
                approved=False,
                continue_onboarding=True
            )
        elif context.get('step') == 'experience':
            return OnboardResponse(
                message="Been to a place like this before?",
                approved=False,
                continue_onboarding=True
            )
        else:
            # Unknown state
            print(f"DEBUG - Unknown step: {context.get('step')}")
            return OnboardResponse(
                message="Something went wrong. Try again.",
                approved=False,
                continue_onboarding=False
            )
    
    # STEP 1: Validate and store age
    if context['step'] == 'age':
        import re
        age_match = re.search(r'\b(\d+)\b', request.message)
        
        if not age_match:
            return OnboardResponse(
                message="Need a number.",
                approved=False,
                continue_onboarding=True
            )
        
        age = int(age_match.group(1))
        
        if age < 18:
            return OnboardResponse(
                message="Too young. Not tonight.",
                approved=False,
                continue_onboarding=False
            )
        
        if age > 80:
            return OnboardResponse(
                message="Wrong place for you.",
                approved=False,
                continue_onboarding=False
            )
        
        # Store age and move to next step
        context['age'] = age
        context['step'] = 'name'
        user.onboarding_context = context
        db.commit()
        
        return OnboardResponse(
            message="What should I call you?",
            approved=False,
            continue_onboarding=True
        )
    
    # STEP 2: Store name
    if context['step'] == 'name':
        name = request.message.strip()
        
        if not name or len(name) > 30:
            return OnboardResponse(
                message="Name?",
                approved=False,
                continue_onboarding=True
            )
        
        context['name'] = name
        context['step'] = 'pronouns'
        user.onboarding_context = context
        db.commit()
        
        return OnboardResponse(
            message="Pronouns? Or skip.",
            approved=False,
            continue_onboarding=True
        )
    
    # STEP 3: Store pronouns (optional)
    if context['step'] == 'pronouns':
        pronouns = request.message.strip().lower()
        
        # Allow skipping
        if pronouns in ['skip', 'none', 'pass', 'n/a', '']:
            context['pronouns'] = None
        else:
            context['pronouns'] = pronouns
        
        context['step'] = 'motivation'
        user.onboarding_context = context
        db.commit()
        
        return OnboardResponse(
            message="What brings you here?",
            approved=False,
            continue_onboarding=True
        )
    
    # STEP 4: Store motivation
    if context['step'] == 'motivation':
        context['motivation'] = request.message.strip()
        context['step'] = 'experience'
        user.onboarding_context = context
        db.commit()
        
        return OnboardResponse(
            message="Been to a place like this before?",
            approved=False,
            continue_onboarding=True
        )
    
    # STEP 5: Store experience and approve
    if context['step'] == 'experience':
        context['experience'] = request.message.strip()
        context['step'] = 'complete'
        user.onboarding_context = context
        db.commit()
        
        return OnboardResponse(
            message="Alright. Head in. Bart's behind the bar.",
            approved=True,
            continue_onboarding=False
        )
    
    # Fallback (shouldn't reach here)
    print(f"DEBUG - Unexpected state. Step: {context.get('step')}, Context: {context}")
    return OnboardResponse(
        message="Something went wrong. Try again.",
        approved=False,
        continue_onboarding=False
    )