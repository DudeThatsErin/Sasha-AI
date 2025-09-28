"""
Model Training for Sasha AI using Hugging Face Transformers
"""

import json
import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    TrainingArguments, 
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset
from typing import List, Dict
import os
from config.app_config import config

class SashaTrainer:
    def __init__(self, model_name: str = None):
        """
        Initialize the trainer with a pre-trained conversational model
        
        Args:
            model_name: Hugging Face model name (DialoGPT, GPT-2, etc.)
        """
        self.model_name = model_name or config.DEFAULT_MODEL_NAME
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        
        # Add padding token if it doesn't exist
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
    
    def prepare_training_data(self, conversations: List[Dict[str, str]]) -> Dataset:
        """
        Prepare conversational data for training
        
        Args:
            conversations: List of {"user": "message", "assistant": "response"} dicts
        
        Returns:
            Dataset ready for training
        """
        # Format conversations for training
        formatted_conversations = []
        
        for conv in conversations:
            # Create a conversation string
            conversation = f"User: {conv['user']} Assistant: {conv['assistant']}{self.tokenizer.eos_token}"
            formatted_conversations.append(conversation)
        
        # Tokenize the conversations
        def tokenize_function(examples):
            return self.tokenizer(
                examples['text'], 
                truncation=True, 
                padding=True, 
                max_length=config.MAX_LENGTH
            )
        
        # Create dataset
        dataset = Dataset.from_dict({'text': formatted_conversations})
        tokenized_dataset = dataset.map(tokenize_function, batched=True)
        
        return tokenized_dataset
    
    def load_training_data_from_file(self, file_path: str = None) -> List[Dict[str, str]]:
        """
        Load training data from a JSON file
        
        Expected format:
        [
            {"user": "message", "assistant": "response"},
            {"user": "message", "assistant": "response"},
            ...
        ]
        """
        file_path = file_path or config.TRAINING_DATA_FILE
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def train(self, training_data: List[Dict[str, str]], output_dir: str = None):
        """
        Train the model on conversational data
        
        Args:
            training_data: List of conversation dictionaries
            output_dir: Directory to save the trained model
        """
        output_dir = output_dir or config.TRAINING_OUTPUT_DIR
        
        print(f"Preparing training data with {len(training_data)} conversations...")
        dataset = self.prepare_training_data(training_data)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            overwrite_output_dir=True,
            num_train_epochs=config.TRAINING_EPOCHS,
            per_device_train_batch_size=config.BATCH_SIZE,
            save_steps=500,
            save_total_limit=2,
            prediction_loss_only=True,
            logging_steps=100,
            logging_dir=f"{config.LOG_DIR}/training_logs",
            warmup_steps=100,
            learning_rate=config.LEARNING_RATE,
        )
        
        # Data collator for language modeling
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,  # We're doing causal LM, not masked LM
        )
        
        # Initialize trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            data_collator=data_collator,
            train_dataset=dataset,
        )
        
        print("Starting training...")
        trainer.train()
        
        print(f"Saving model to {output_dir}...")
        trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)
        
        print("Training completed!")
        return output_dir

def train_with_sample_data():
    """
    Train model with sample data - useful for initial setup
    """
    trainer = SashaTrainer()
    
    # Load sample training data
    training_data = trainer.load_training_data_from_file()
    
    # Train the model
    trainer.train(training_data)
    
    print("\nTraining complete! You can now use the trained model in your FastAPI app.")
    print("The model has been saved to:", config.TRAINING_OUTPUT_DIR)

if __name__ == "__main__":
    train_with_sample_data()
