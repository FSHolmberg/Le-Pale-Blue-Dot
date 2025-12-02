#!/usr/bin/env python3
"""
Interactive terminal interface for LPBD agents.
"""

from time import time

from src.router import Router
from src.schemas.message import Message


def main():
    print("=" * 60)
    print("LPBD Interactive Terminal")
    print("=" * 60)
    print("\nType your message and press Enter.")
    print("Type 'exit' or 'quit' to stop.\n")
    print("All messages logged to: logs/lpbd.log\n")
    print("=" * 60)
    
    router = Router()  # CREATE ONCE HERE
    
    while True:
        try:
            message = input("\nYou: ").strip()
            
            if not message:
                continue
                
            if message.lower() in ["exit", "quit", "q"]:
                print("\nGoodbye.\n")
                break
            
            # Use the same router instance
            msg = Message(
                user_id="test_user",
                text=message,
                timestamp=time()
            )
            
            agent_name, reply = router.handle(msg)
            print(f"\n{agent_name.upper()}: {reply}\n")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye.\n")
            break
        except Exception as e:
            print(f"\nUnexpected error: {e}\n")


if __name__ == "__main__":
    main()