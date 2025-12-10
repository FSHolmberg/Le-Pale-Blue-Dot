from src.database.models import SessionLocal, Message, Session as SessionModel, User
from src.database.memory_manager import MemoryManager
from datetime import datetime
import uuid

db = SessionLocal()

# Create test user
user = User(
    id=str(uuid.uuid4()),
    anonymous_id="test_user_123"
)
db.add(user)
db.commit()

# Create test session
session = SessionModel(
    id=str(uuid.uuid4()),
    user_id=user.id,
    status="active"
)
db.add(session)
db.commit()

# Add some test messages
msg1 = Message(
    session_id=session.id,
    agent="user",
    content="I'm feeling anxious about work",
    is_user_message=1
)
msg2 = Message(
    session_id=session.id,
    agent="bart",
    content="Tell me what's going on with work."
)
msg3 = Message(
    session_id=session.id,
    agent="user",
    content="My boss is demanding impossible deadlines",
    is_user_message=1
)

db.add_all([msg1, msg2, msg3])
db.commit()

# Test memory manager
mgr = MemoryManager(db)

# Get hot storage
hot = mgr.get_hot_storage(session.id)
print(f"Hot storage messages: {len(hot)}")
for msg in hot:
    print(f"  {msg['agent']}: {msg['content']}")

# Get full context and format
context = mgr.get_full_context(user.id, session.id)
formatted = mgr.format_for_agent_context(context)
print("\nFormatted context:")
print(formatted)

db.close()