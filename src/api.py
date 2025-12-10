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

@app.post("/session/start", response_model=SessionStartResponse)
async def start_session(
    username: str = Depends(verify_credentials),
    db: DBSession = Depends(get_db)):
    
    # Create user (for now, each session = new anonymous user)
    user = User(
        anonymous_id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc))
    db.add(user)
    db.commit()
    
    # Get weather
    weather = get_calais_environment()
    
    # Create session
    session = Session(
        user_id=user.id,
        started_at=datetime.now(timezone.utc),
        status="active",
        weather=weather,
        message_count=0)
    
    db.add(session)
    db.commit()
    
    return SessionStartResponse(
        session_id=session.id,
        weather=weather,
        available_agents=["bart", "bernie", "jb", "blanca", "hermes"],
        timestamp=datetime.now(timezone.utc).isoformat())

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
    
    # Initialize Router
    router = Router()
    
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
        # Auto-routing
        agent_name, agent_response = router.handle(msg, db_session=db)
    
    # Detect handoff in response and store for next message
    handoff_target = router._detect_handoff(agent_response)
    if handoff_target:
        session.pending_handoff = handoff_target
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
    Handle onboarding conversation with Blanca at the exterior.
    Multi-turn conversation until user is approved or rejected.
    """
    
    # Get or create user
    user = db.query(User).filter_by(anonymous_id=request.anonymous_id).first()
    if not user:
        user = User(anonymous_id=request.anonymous_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Check if user has completed sessions (recurring vs new)
    completed_sessions = db.query(Session).filter_by(
        user_id=user.id,
        status="ended"
    ).count()
    
    is_new_user = completed_sessions == 0
    
    # Get or create onboarding session
    # Use a special session type or flag to track onboarding state
    onboarding_session = db.query(Session).filter_by(
        user_id=user.id,
        status="onboarding"
    ).first()
    
    if not onboarding_session:
        onboarding_session = Session(
            user_id=user.id,
            status="onboarding"
        )
        db.add(onboarding_session)
        db.commit()
        db.refresh(onboarding_session)
    
    # Load onboarding context
    config = Config()
    onboarding_config = config.get_onboarding_context(is_new_user)
    
    # Get conversation history from this onboarding session
    previous_messages = db.query(DBMessage).filter_by(
        session_id=onboarding_session.id
    ).order_by(DBMessage.timestamp).all()
    
    # Build conversation history for Blanca
    conversation_history = []
    for msg in previous_messages:
        role = "user" if msg.is_user_message else "assistant"
        conversation_history.append({
            "role": role,
            "content": msg.content
        })
    
    # If this is initial request (no message), get Blanca's opening
    if request.message is None:
        blanca_prompt = config.get_prompt("blanca")
        blanca_prompt += f"\n\n{onboarding_config}"
        
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            system=blanca_prompt,
            messages=[{
                "role": "user",
                "content": "A new person just approached the door."
            }]
        )
        
        blanca_message = response.content[0].text
        
        # Save Blanca's message
        msg = DBMessage(
            session_id=onboarding_session.id,
            agent="blanca",
            content=blanca_message,
            is_user_message=0
        )
        db.add(msg)
        db.commit()
        
        return OnboardResponse(
            message=blanca_message,
            approved=False,
            continue_onboarding=True
        )
    
    # User has responded, save their message
    user_msg = DBMessage(
        session_id=onboarding_session.id,
        agent="user",
        content=request.message,
        is_user_message=1
    )
    db.add(user_msg)
    db.commit()
    
    # Add user message to conversation history
    conversation_history.append({
        "role": "user",
        "content": request.message
    })
    
    # Get Blanca's response with full context
    blanca_prompt = config.get_prompt("blanca")
    blanca_prompt += f"\n\n{onboarding_config}"
    
   
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=150,
        system=blanca_prompt,
        messages=conversation_history
    )
    
    blanca_message = response.content[0].text
    
    # Save Blanca's response
    msg = DBMessage(
        session_id=onboarding_session.id,
        agent="blanca",
        content=blanca_message,
        is_user_message=0
    )
    db.add(msg)
    db.commit()
    
    # Check if Blanca approved/rejected
    # Look for approval/rejection signals in her response
    approved = False
    continue_onboarding = True
    
    blanca_lower = blanca_message.lower()
    
    # Approval signals
    if any(phrase in blanca_lower for phrase in [
        "welcome in", "alright, welcome", "go on in", "door's open", 
        "go have a drink", "head on in"
    ]):
        approved = True
        continue_onboarding = False
        # Mark onboarding session as complete
        onboarding_session.status = "completed"
        db.commit()
    
    # Rejection signals
    elif any(phrase in blanca_lower for phrase in [
        "sorry, not tonight", "not today", "can't let you in", 
        "come back when", "not the right place"
    ]):
        approved = False
        continue_onboarding = False
        # Mark onboarding session as rejected
        onboarding_session.status = "rejected"
        db.commit()
    
    return OnboardResponse(
        message=blanca_message,
        approved=approved,
        continue_onboarding=continue_onboarding
    )