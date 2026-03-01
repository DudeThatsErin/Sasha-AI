"""
Conversation Collector for Sasha AI v2
Collects and manages conversations for review.
"""

import json
import os
from datetime import datetime
from typing import List, Dict
from config.app_config import config


class ConversationCollector:
    def __init__(self, storage_file: str = None):
        self.storage_file = storage_file or config.COLLECTED_CONVERSATIONS_FILE
        self.conversations: List[Dict] = []
        self.load_conversations()

    def load_conversations(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    self.conversations = json.load(f)
            except Exception as e:
                print(f"Error loading conversations: {e}")
                self.conversations = []
        else:
            self.conversations = []

    def save_conversations(self):
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(self.conversations, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving conversations: {e}")

    def add_conversation(self, user_message: str, assistant_response: str, chat_id: str):
        self.conversations.append(
            {
                "user_message": user_message,
                "assistant_response": assistant_response,
                "timestamp": datetime.now().isoformat(),
                "chat_id": chat_id,
            }
        )
        self.save_conversations()

    def get_conversation_stats(self) -> Dict:
        total = len(self.conversations)
        return {
            "total_conversations": total,
            "unique_chats": len(set(c["chat_id"] for c in self.conversations)) if total else 0,
        }

    def clear_conversations(self):
        self.conversations = []
        self.save_conversations()


collector = ConversationCollector()
