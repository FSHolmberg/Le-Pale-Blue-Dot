from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DBSession
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import time

from src.router import Router
from src.schemas.message import Message
from src.calais_weather import get_calais_environment
from src.database.models import get_db, User, Session, Message as DBMessage

app = FastAPI(title="Le Pale Blue Dot API")

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

# --- Endpoints ---

@app.post("/session/start", response_model=SessionStartResponse)
def start_session(db: DBSession = Depends(get_db)):
    # Create user (for now, each session = new anonymous user)
    user = User(
        anonymous_id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc)
    )
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
        message_count=0
    )
    db.add(session)
    db.commit()
    
    return SessionStartResponse(
        session_id=session.id,
        weather=weather,
        available_agents=["bart", "bernie", "jb", "blanca", "hermes"],
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@app.post("/message", response_model=MessageResponse)
def send_message(request: MessageRequest, db: DBSession = Depends(get_db)):
    # Get session from database
    session = db.query(Session).filter(Session.id == request.session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check session status
    if session.status in ["kicked", "ended"]:
        raise HTTPException(
            status_code=403,
            detail=f"Session has {session.status}. Start a new session."
        )
    
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
    
    # Get conversation history for Router
    messages = db.query(DBMessage).filter(DBMessage.session_id == session.id).all()
    
    # Initialize Router (TODO: store Router state in session or reconstruct?)
    router = Router()
    
    # Build Message for Router
    msg = Message(
        user_id=request.session_id,
        text=request.content,
        timestamp=time.time()
    )
    
    # Get agent response
    agent_name, agent_response = router.handle(msg)
    
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