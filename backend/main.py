"""
Sasha AI - Complete FastAPI Backend with Learning Capabilities
Combines all functionality: basic chat, model training, continuous learning, and auto-retraining
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from typing import List, Optional

# Import our organized modules
from config.app_config import config
from lib.model_manager import model_manager
from lib.conversation_collector import collector
from lib.model_trainer import SashaTrainer

app = FastAPI(title="Sasha AI Bot - Complete", version="2.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class MessageRequest(BaseModel):
    message: str
    chat_id: str

class MessageResponse(BaseModel):
    response: str
    chat_id: str

class FeedbackRequest(BaseModel):
    conversation_index: int
    feedback: str  # "good" or "bad"

class RetrainRequest(BaseModel):
    use_feedback_filter: Optional[str] = None  # "good", "bad", or None
    epochs: int = 3

@app.on_event("startup")
async def startup_event():
    """Initialize the model when the app starts"""
    print("Starting Sasha AI Bot...")
    model_manager.load_model()
    print("Sasha AI Bot ready!")

@app.get("/")
async def root():
    """Root endpoint with status information"""
    model_status = "trained model" if model_manager.use_trained_model else "fallback responses"
    stats = collector.get_conversation_stats()
    return {
        "message": f"Sasha AI Bot is running with {model_status}!",
        "version": "2.0.0",
        "collected_conversations": stats["total_conversations"],
        "model_status": model_manager.get_status()
    }

@app.post("/chat", response_model=MessageResponse)
async def chat(request: MessageRequest):
    """
    Main chat endpoint - generates responses and collects conversations for learning
    """
    try:
        # Generate response using model manager
        bot_response = model_manager.generate_response(request.message)
        
        # Collect the conversation for future training
        collector.add_conversation(
            user_message=request.message,
            assistant_response=bot_response,
            chat_id=request.chat_id
        )
        
        return MessageResponse(
            response=bot_response,
            chat_id=request.chat_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === CONVERSATION MANAGEMENT ENDPOINTS ===

@app.post("/feedback")
async def add_feedback(request: FeedbackRequest):
    """Add feedback to a conversation for quality control"""
    success = collector.add_feedback(request.conversation_index, request.feedback)
    if success:
        return {"message": "Feedback added successfully"}
    else:
        raise HTTPException(status_code=404, detail="Conversation not found")

@app.get("/conversations/stats")
async def get_conversation_stats():
    """Get statistics about collected conversations"""
    return collector.get_conversation_stats()

@app.get("/conversations/export")
async def export_conversations(feedback_filter: Optional[str] = None):
    """Export conversations as training data"""
    try:
        filename = collector.export_training_data(
            filename=f"./config/exported_training_data_{feedback_filter or 'all'}.json",
            include_feedback=feedback_filter
        )
        return {"message": f"Conversations exported to {filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/conversations")
async def clear_conversations():
    """Clear all collected conversations"""
    collector.clear_conversations()
    return {"message": "All conversations cleared"}

# === MODEL MANAGEMENT ENDPOINTS ===

@app.get("/model/status")
async def model_status():
    """Get detailed model and conversation status"""
    model_info = model_manager.get_status()
    conversation_stats = collector.get_conversation_stats()
    
    return {
        "model": model_info,
        "conversations": conversation_stats,
        "config": {
            "min_conversations_for_retrain": config.MIN_CONVERSATIONS_FOR_RETRAIN,
            "retrain_interval_hours": config.RETRAIN_INTERVAL_HOURS,
            "training_epochs": config.TRAINING_EPOCHS
        }
    }

@app.post("/model/reload")
async def reload_model():
    """Reload the trained model"""
    model_manager.load_model()
    return {
        "message": "Model reloaded",
        "status": model_manager.get_status()
    }

# === TRAINING ENDPOINTS ===

@app.post("/train/initial")
async def train_initial_model():
    """Train the initial model using sample training data"""
    try:
        trainer = SashaTrainer()
        training_data = trainer.load_training_data_from_file()
        
        print(f"Training initial model with {len(training_data)} sample conversations...")
        trainer.train(training_data)
        
        # Reload the model
        model_manager.load_model()
        
        return {
            "message": "Initial model training completed!",
            "training_data_size": len(training_data),
            "model_status": model_manager.get_status()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Initial training failed: {str(e)}")

@app.post("/train/retrain")
async def retrain_model(request: RetrainRequest):
    """Retrain the model using collected conversations"""
    try:
        # Get training data from collected conversations
        training_data = collector.get_training_data(include_feedback=request.use_feedback_filter)
        
        if len(training_data) < 5:
            raise HTTPException(
                status_code=400, 
                detail=f"Not enough training data. Need at least 5 conversations, got {len(training_data)}"
            )
        
        # Load existing training data and combine
        try:
            with open(config.TRAINING_DATA_FILE, 'r') as f:
                existing_data = json.load(f)
                training_data.extend(existing_data)
                print(f"Added {len(existing_data)} existing training examples")
        except FileNotFoundError:
            print("No existing training data found, using only collected conversations")
        
        print(f"Starting retraining with {len(training_data)} conversations...")
        
        # Train the model
        trainer = SashaTrainer()
        new_model_path = f"{config.TRAINING_OUTPUT_DIR}_retrained"
        trainer.train(training_data, output_dir=new_model_path)
        
        # Replace the current model
        success = model_manager.replace_model(new_model_path)
        
        if success:
            return {
                "message": "Model retrained successfully!",
                "training_data_size": len(training_data),
                "epochs": request.epochs,
                "model_status": model_manager.get_status()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to replace model after training")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retraining failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model_manager.use_trained_model,
        "conversations_collected": len(collector.conversations)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)