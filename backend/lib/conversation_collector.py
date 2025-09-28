"""
Conversation Collector for Sasha AI
Collects and manages conversations for training data
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel
from config.app_config import config

class ConversationEntry(BaseModel):
    user_message: str
    assistant_response: str
    timestamp: datetime
    chat_id: str
    feedback: Optional[str] = None  # "good", "bad", or None

class ConversationCollector:
    def __init__(self, storage_file: str = None):
        self.storage_file = storage_file or config.COLLECTED_CONVERSATIONS_FILE
        self.conversations: List[Dict] = []
        self.load_conversations()
    
    def load_conversations(self):
        """Load existing conversations from file"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    self.conversations = json.load(f)
                print(f"Loaded {len(self.conversations)} existing conversations")
            except Exception as e:
                print(f"Error loading conversations: {e}")
                self.conversations = []
        else:
            self.conversations = []
    
    def save_conversations(self):
        """Save conversations to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversations, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving conversations: {e}")
    
    def add_conversation(self, user_message: str, assistant_response: str, chat_id: str):
        """Add a new conversation entry"""
        conversation = {
            "user_message": user_message,
            "assistant_response": assistant_response,
            "timestamp": datetime.now().isoformat(),
            "chat_id": chat_id,
            "feedback": None
        }
        
        self.conversations.append(conversation)
        self.save_conversations()
        print(f"Added conversation to collection. Total: {len(self.conversations)}")
    
    def add_feedback(self, conversation_index: int, feedback: str):
        """Add feedback to a conversation (good/bad)"""
        if 0 <= conversation_index < len(self.conversations):
            self.conversations[conversation_index]["feedback"] = feedback
            self.save_conversations()
            return True
        return False
    
    def get_training_data(self, include_feedback: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Convert collected conversations to training format
        
        Args:
            include_feedback: Filter by feedback ("good", "bad", or None for all)
        
        Returns:
            List of {"user": "message", "assistant": "response"} dicts
        """
        training_data = []
        
        for conv in self.conversations:
            # Filter by feedback if specified
            if include_feedback is not None and conv.get("feedback") != include_feedback:
                continue
            
            training_data.append({
                "user": conv["user_message"],
                "assistant": conv["assistant_response"]
            })
        
        return training_data
    
    def export_training_data(self, filename: str = None, include_feedback: Optional[str] = None):
        """Export conversations as training data"""
        if filename is None:
            filename = f"./config/exported_training_data_{include_feedback or 'all'}.json"
        
        training_data = self.get_training_data(include_feedback)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, indent=2)
        
        print(f"Exported {len(training_data)} conversations to {filename}")
        return filename
    
    def get_conversation_stats(self) -> Dict:
        """Get statistics about collected conversations"""
        total = len(self.conversations)
        good_feedback = len([c for c in self.conversations if c.get("feedback") == "good"])
        bad_feedback = len([c for c in self.conversations if c.get("feedback") == "bad"])
        no_feedback = total - good_feedback - bad_feedback
        
        return {
            "total_conversations": total,
            "good_feedback": good_feedback,
            "bad_feedback": bad_feedback,
            "no_feedback": no_feedback,
            "unique_chats": len(set(c["chat_id"] for c in self.conversations))
        }
    
    def clear_conversations(self):
        """Clear all collected conversations"""
        self.conversations = []
        self.save_conversations()
        print("All conversations cleared")

# Global collector instance
collector = ConversationCollector()
