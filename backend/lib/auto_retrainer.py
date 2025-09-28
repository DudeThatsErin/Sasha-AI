"""
Automatic Retraining for Sasha AI
Monitors conversation collection and automatically retrains when enough data is available
"""

import time
import schedule
import json
import os
from datetime import datetime
from lib.conversation_collector import collector
from lib.model_trainer import SashaTrainer
from lib.model_manager import model_manager
from config.app_config import config

class AutoRetrainer:
    def __init__(self):
        self.last_retrain_count = 0
        
    def should_retrain(self) -> bool:
        """Check if we should retrain based on new conversations"""
        stats = collector.get_conversation_stats()
        current_count = stats["total_conversations"]
        
        # Check if we have enough new conversations
        new_conversations = current_count - self.last_retrain_count
        
        print(f"Current conversations: {current_count}, Last retrain: {self.last_retrain_count}")
        print(f"New conversations: {new_conversations}, Minimum needed: {config.MIN_CONVERSATIONS_FOR_RETRAIN}")
        
        return new_conversations >= config.MIN_CONVERSATIONS_FOR_RETRAIN
    
    def retrain_model(self) -> bool:
        """Perform automatic retraining"""
        try:
            print(f"[{datetime.now()}] Starting automatic retraining...")
            
            # Get training data (only use conversations with good feedback or no feedback)
            good_conversations = collector.get_training_data(include_feedback="good")
            neutral_conversations = collector.get_training_data(include_feedback=None)
            
            # Combine good and neutral conversations
            training_data = good_conversations + neutral_conversations
            
            if len(training_data) < 5:
                print(f"Not enough quality training data: {len(training_data)}")
                return False
            
            # Load existing training data
            try:
                with open(config.TRAINING_DATA_FILE, 'r') as f:
                    existing_data = json.load(f)
                    training_data.extend(existing_data)
                    print(f"Added {len(existing_data)} existing training examples")
            except FileNotFoundError:
                print("No existing training data found")
            
            # Initialize trainer and retrain
            trainer = SashaTrainer()
            new_model_path = f"{config.TRAINING_OUTPUT_DIR}_new"
            trainer.train(training_data, output_dir=new_model_path)
            
            # Replace current model
            success = model_manager.replace_model(new_model_path)
            
            if success:
                # Update last retrain count
                stats = collector.get_conversation_stats()
                self.last_retrain_count = stats["total_conversations"]
                
                print(f"[{datetime.now()}] Retraining completed successfully!")
                print(f"Trained on {len(training_data)} conversations")
                return True
            else:
                print(f"[{datetime.now()}] Failed to replace model")
                return False
            
        except Exception as e:
            print(f"[{datetime.now()}] Retraining failed: {e}")
            return False
    
    def check_and_retrain(self):
        """Check if retraining is needed and do it"""
        if self.should_retrain():
            print("Retraining conditions met, starting retraining...")
            self.retrain_model()
        else:
            print("Retraining not needed yet")
    
    def start_monitoring(self):
        """Start the automatic retraining monitor"""
        print(f"Starting auto-retrainer...")
        print(f"Will retrain every {config.RETRAIN_INTERVAL_HOURS} hours if {config.MIN_CONVERSATIONS_FOR_RETRAIN} new conversations are available")
        
        # Schedule the retraining check
        schedule.every(config.RETRAIN_INTERVAL_HOURS).hours.do(self.check_and_retrain)
        
        # Initial check
        self.check_and_retrain()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

# Global auto retrainer instance
auto_retrainer = AutoRetrainer()

def main():
    """Run the auto retrainer"""
    auto_retrainer.start_monitoring()

if __name__ == "__main__":
    main()
