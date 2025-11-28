#!/usr/bin/env python3
"""
Interactive terminal interface for LPBD agents.

Usage:
    python send.py

Then just type messages. Type 'exit' or 'quit' to stop.
All messages are logged to logs/lpbd.log for later analysis.
"""

from time import time

from src.router import Router
from src.schemas.message import Message



def send_message(text: str, user_id: str = "test_user") -> None:
    """
    Send a message through the router and print the response.
    
    Args:
        text: Message to send
        user_id: User identifier (defaults to test_user)
    """
    router = Router()
    
    msg = Message(
        user_id=user_id,
        text=text,
        timestamp=time()
    )
    
    try:
        agent_name, reply = router.handle(msg)
        
        # Print response cleanly (no log prefix)
        print(f"\n{agent_name.upper()}: {reply}\n")
        
    except Exception as e:
        print(f"\nError: {e}\n")


def main():
    print("=" * 60)
    print("LPBD Interactive Terminal")
    print("=" * 60)
    print("\nType your message and press Enter.")
    print("Type 'exit' or 'quit' to stop.\n")
    print("All messages logged to: logs/lpbd.log\n")
    print("=" * 60)
    
    while True:
        try:
            message = input("\nYou: ").strip()
            
            if not message:
                continue
                
            if message.lower() in ["exit", "quit", "q"]:
                print("\nGoodbye.\n")
                break
            
            send_message(message)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye.\n")
            break
        except Exception as e:
            print(f"\nUnexpected error: {e}\n")


if __name__ == "__main__":
    main()