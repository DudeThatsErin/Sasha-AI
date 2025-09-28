"""
Model Management for Sasha AI
Handles loading, generating responses, and managing model lifecycle
"""

import os
import torch
import random
import shutil
from datetime import datetime
from typing import Optional
from transformers import AutoTokenizer, AutoModelForCausalLM
from config.app_config import config

class ModelManager:
    def __init__(self):
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModelForCausalLM] = None
        self.use_trained_model = False
        self.fallback_responses = [
            "That's interesting! Tell me more.",
            "I understand what you're saying.",
            "Thanks for sharing that with me!",
            "How does that make you feel?",
            "That's a great point!",
            "I'm here to help with whatever you need.",
            "Can you elaborate on that?",
            "That sounds important to you.",
            "I appreciate you telling me that.",
            "What would you like to explore next?"
        ]
    
    def load_model(self, model_path: str = None):
        """Load the trained model if it exists"""
        model_path = model_path or config.get_model_path()
        
        try:
            if os.path.exists(model_path):
                print(f"Loading trained model from {model_path}...")
                self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                self.model = AutoModelForCausalLM.from_pretrained(model_path)
                self.use_trained_model = True
                print("Trained model loaded successfully!")
            else:
                print(f"No trained model found at {model_path}. Using fallback responses.")
                self.use_trained_model = False
        except Exception as e:
            print(f"Error loading model: {e}. Using fallback responses.")
            self.use_trained_model = False
    
    def generate_response(self, user_message: str) -> str:
        """Generate response using the trained model or fallback"""
        if not self.use_trained_model or self.tokenizer is None or self.model is None:
            return random.choice(self.fallback_responses)
        
        try:
            # Format the input
            input_text = f"User: {user_message} Assistant:"
            
            # Tokenize
            inputs = self.tokenizer.encode(input_text, return_tensors="pt")
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=inputs.shape[1] + config.MAX_NEW_TOKENS,
                    num_return_sequences=1,
                    temperature=config.TEMPERATURE,
                    do_sample=config.DO_SAMPLE,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )
            
            # Decode the response
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract just the assistant's response
            if "Assistant:" in full_response:
                response = full_response.split("Assistant:")[-1].strip()
                # Clean up the response
                if "User:" in response:
                    response = response.split("User:")[0].strip()
                return response if response else random.choice(self.fallback_responses)
            else:
                return random.choice(self.fallback_responses)
                
        except Exception as e:
            print(f"Error generating response: {e}")
            return random.choice(self.fallback_responses)
    
    def backup_current_model(self) -> Optional[str]:
        """Backup the current model before replacing it"""
        model_path = config.get_model_path()
        
        if not os.path.exists(model_path):
            return None
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = config.get_backup_path(timestamp)
            
            # Ensure backup directory exists
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            shutil.copytree(model_path, backup_path)
            print(f"Model backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"Error backing up model: {e}")
            return None
    
    def replace_model(self, new_model_path: str) -> bool:
        """Replace the current model with a new one"""
        try:
            # Backup current model
            if config.BACKUP_MODELS:
                self.backup_current_model()
            
            # Remove old model
            model_path = config.get_model_path()
            if os.path.exists(model_path):
                shutil.rmtree(model_path)
            
            # Move new model to current location
            shutil.move(new_model_path, model_path)
            
            # Reload the model
            self.load_model()
            
            print(f"Model successfully replaced and reloaded")
            return True
            
        except Exception as e:
            print(f"Error replacing model: {e}")
            return False
    
    def get_status(self) -> dict:
        """Get current model status"""
        return {
            "using_trained_model": self.use_trained_model,
            "model_path": config.get_model_path() if self.use_trained_model else None,
            "model_exists": os.path.exists(config.get_model_path()),
            "fallback_responses_count": len(self.fallback_responses)
        }

# Global model manager instance
model_manager = ModelManager()
