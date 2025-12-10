from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from src.database.models import Message, MessageArchive, Session as SessionModel
from datetime import datetime

class MemoryManager:
    def __init__(self, db: Session):
        self.db = db
    
    # HOT STORAGE: Current session
    def get_hot_storage(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
        """Get messages from current active session"""
        query = self.db.query(Message)\
            .filter(Message.session_id == session_id)\
            .order_by(Message.timestamp.asc())
        
        if limit:
            query = query.limit(limit)
        
        messages = query.all()
        
        return [
            {
                "agent": msg.agent,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "is_user": bool(msg.is_user_message)
            }
            for msg in messages
        ]
    
    # COLD STORAGE: Last N sessions
    def get_cold_storage(self, user_id: str, max_sessions: int = 4) -> List[Dict]:
        """
        Get last N completed sessions from archive (3 first + 10 last messages per session)
        """
        # Get last N completed session_ids for this user
        recent_sessions = self.db.query(SessionModel.id)\
            .filter(SessionModel.user_id == user_id)\
            .filter(SessionModel.status.in_(["completed", "ended"]))\
            .order_by(desc(SessionModel.ended_at))\
            .limit(max_sessions)\
            .all()
        
        if not recent_sessions:
            return []
        
        session_ids = [s.id for s in recent_sessions]
        
        # Get archived messages from these sessions
        archives = self.db.query(MessageArchive)\
            .filter(MessageArchive.session_id.in_(session_ids))\
            .order_by(
                desc(MessageArchive.session_id),
                MessageArchive.message_position.asc(),
                MessageArchive.position_index.asc()
            )\
            .all()
        
        return [
            {
                "agent": arc.agent,
                "content": arc.content,
                "timestamp": arc.timestamp,
                "is_user": bool(arc.is_user_message),
                "session_id": arc.session_id
            }
            for arc in archives
        ]
    
    # ARCHIVING: Move session to cold storage
    def archive_session(self, session_id: str):
        """
        Archive session: first 3 + last 10 messages
        Call when session ends
        """
        # Get all messages from session
        all_messages = self.db.query(Message)\
            .filter(Message.session_id == session_id)\
            .order_by(Message.timestamp.asc())\
            .all()
        
        if len(all_messages) == 0:
            return
        
        # Get session for user_id
        session = self.db.query(SessionModel)\
            .filter(SessionModel.id == session_id)\
            .first()
        
        if not session:
            return
        
        # Archive first 3 messages
        opening_messages = all_messages[:3]
        for idx, msg in enumerate(opening_messages, 1):
            archive = MessageArchive(
                session_id=session_id,
                user_id=session.user_id,
                agent=msg.agent,
                content=msg.content,
                timestamp=msg.timestamp,
                is_user_message=msg.is_user_message,
                message_position='opening',
                position_index=idx
            )
            self.db.add(archive)
        
        # Archive last 10 messages (or 5 for space savings)
        closing_messages = all_messages[-10:]
        for idx, msg in enumerate(closing_messages, 1):
            archive = MessageArchive(
                session_id=session_id,
                user_id=session.user_id,
                agent=msg.agent,
                content=msg.content,
                timestamp=msg.timestamp,
                is_user_message=msg.is_user_message,
                message_position='closing',
                position_index=idx
            )
            self.db.add(archive)
        
        self.db.commit()
    
    # COMBINED CONTEXT
    def get_full_context(self, user_id: str, session_id: str, 
                        max_cold_sessions: int = 4) -> List[Dict]:
        """
        Returns: Cold storage (last 4 sessions) + Hot storage (current session)
        """
        cold = self.get_cold_storage(user_id, max_cold_sessions)
        hot = self.get_hot_storage(session_id)
        
        return cold + hot
    
    def format_for_agent_context(self, messages: List[Dict], 
                                 max_tokens: int = 5000) -> str:
        """
        Format messages for injection into agent system prompt
        Includes basic token limiting (rough estimate: ~4 chars = 1 token)
        """
        if not messages:
            return ""
        
        formatted_lines = ["=== Previous Conversation Context ==="]
        total_chars = 0
        max_chars = max_tokens * 4  # Rough estimate
        
        for msg in messages:
            role = "User" if msg['is_user'] else msg['agent'].title()
            line = f"{role}: {msg['content']}"
            
            # Basic token limiting
            if total_chars + len(line) > max_chars:
                formatted_lines.append("(earlier messages truncated...)")
                break
            
            formatted_lines.append(line)
            total_chars += len(line)
        
        formatted_lines.append("=== End Context ===\n")
        return "\n".join(formatted_lines)