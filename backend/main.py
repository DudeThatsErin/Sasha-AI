from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
from typing import List

app = FastAPI(title="Sasha AI Bot", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
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

# Simple bot responses
BOT_RESPONSES = [
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

@app.get("/")
async def root():
    return {"message": "Sasha AI Bot is running!"}

@app.post("/chat", response_model=MessageResponse)
async def chat(request: MessageRequest):
    """
    Simple bot that responds to user messages with random responses
    """
    try:
        # Simple bot logic - just return a random response
        bot_response = random.choice(BOT_RESPONSES)
        
        return MessageResponse(
            response=bot_response,
            chat_id=request.chat_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)