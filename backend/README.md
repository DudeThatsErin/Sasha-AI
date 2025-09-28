# Sasha AI Backend

A complete FastAPI backend for Sasha AI with training, continuous learning, and automatic retraining capabilities.

## 📁 Project Structure

```
backend/
├── config/                          # Configuration files
│   ├── app_config.py               # Main configuration settings
│   ├── training_data.json          # Sample training conversations
│   └── collected_conversations.json # Auto-collected conversations (created at runtime)
├── lib/                            # Core library modules
│   ├── conversation_collector.py   # Manages conversation collection
│   ├── model_trainer.py           # Handles model training
│   ├── model_manager.py           # Manages model loading and inference
│   └── auto_retrainer.py          # Automatic retraining logic
├── models/                         # Model storage
│   ├── sasha_model/               # Current trained model (created after training)
│   └── backups/                   # Model backups
├── logs/                          # Training and application logs
├── scripts/                       # Utility scripts
│   ├── train_initial.py          # Train initial model
│   └── start_auto_retrain.py     # Start auto-retraining monitor
├── main.py                        # Complete FastAPI application
└── requirements_training.txt      # All dependencies
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_training.txt
```

### 2. Train Initial Model (Optional)
```bash
python scripts/train_initial.py
```

### 3. Start the Server
```bash
python main.py
```

### 4. Start Auto-Retraining (Optional)
```bash
python scripts/start_auto_retrain.py
```

## 🎯 Features

### Core Chat API
- **POST /chat** - Send messages and get responses
- **GET /** - Server status and information
- **GET /health** - Health check

### Conversation Management
- **GET /conversations/stats** - View conversation statistics
- **GET /conversations/export** - Export conversations as training data
- **POST /feedback** - Add quality feedback to conversations
- **DELETE /conversations** - Clear all collected conversations

### Model Management
- **GET /model/status** - Detailed model and training status
- **POST /model/reload** - Reload the trained model

### Training
- **POST /train/initial** - Train initial model with sample data
- **POST /train/retrain** - Retrain with collected conversations

## 📊 API Examples

### Basic Chat
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "chat_id": "test-chat"}'
```

### Check Status
```bash
curl "http://localhost:8000/model/status"
```

### Retrain Model
```bash
curl -X POST "http://localhost:8000/train/retrain" \
  -H "Content-Type: application/json" \
  -d '{"use_feedback_filter": "good", "epochs": 3}'
```

## ⚙️ Configuration

Edit `config/app_config.py` to customize:

- **Model settings**: Model paths, backup locations
- **Training parameters**: Epochs, batch size, learning rate
- **Auto-retraining**: Conversation thresholds, intervals
- **API settings**: Host, port, CORS origins

## 🔄 Learning Workflow

1. **Chat**: Users interact with Sasha through the frontend
2. **Collect**: Every conversation is automatically saved
3. **Filter**: Optional feedback system for quality control
4. **Retrain**: Automatic or manual retraining with new data
5. **Update**: New model replaces old one seamlessly

## 🛠️ Development

### Manual Training
```python
from lib.model_trainer import SashaTrainer

trainer = SashaTrainer()
training_data = [
    {"user": "Hello", "assistant": "Hi there!"},
    # ... more conversations
]
trainer.train(training_data)
```

### Custom Configuration
```python
from config.app_config import config

# Modify settings
config.TRAINING_EPOCHS = 5
config.MIN_CONVERSATIONS_FOR_RETRAIN = 50
```

### Add Custom Training Data
Edit `config/training_data.json` with your conversations:
```json
[
  {"user": "Your question", "assistant": "Sasha's response"},
  {"user": "Another question", "assistant": "Another response"}
]
```

## 📈 Monitoring

### View Logs
- Training logs: `logs/training_logs/`
- Application logs: Console output

### Check Conversation Stats
```bash
curl "http://localhost:8000/conversations/stats"
```

Response:
```json
{
  "total_conversations": 45,
  "good_feedback": 12,
  "bad_feedback": 3,
  "no_feedback": 30,
  "unique_chats": 8
}
```

## 🔧 Troubleshooting

### Model Not Loading
- Check if `models/sasha_model/` exists
- Train initial model: `python scripts/train_initial.py`

### Training Fails
- Ensure GPU/CPU has enough memory
- Reduce batch size in `config/app_config.py`
- Check training data format

### Import Errors
- Ensure all dependencies installed: `pip install -r requirements_training.txt`
- Check Python path and module structure

## 🚀 Production Deployment

1. **Environment Variables**:
   ```bash
   export SASHA_ENV=production
   ```

2. **Database**: Replace JSON files with proper database
3. **Logging**: Configure proper logging system
4. **Monitoring**: Add health checks and metrics
5. **Security**: Add authentication and rate limiting

## 🌐 Production Deployment with Cloudflare Tunnel

For interviews, demos, or making your local backend accessible from anywhere, use Cloudflare Tunnel:

### **Setup Cloudflare Tunnel**

1. **Install cloudflared:**
   ```bash
   # Windows: Download from https://github.com/cloudflare/cloudflared/releases
   # Or use chocolatey: choco install cloudflared
   ```

2. **Login to Cloudflare:**
   ```bash
   cloudflared tunnel login
   ```

3. **Create a tunnel:**
   ```bash
   cloudflared tunnel create sasha-ai-backend
   ```

4. **Create config file** (`config.yml`):
   ```yaml
   tunnel: sasha-ai-backend
   credentials-file: C:\Users\[username]\.cloudflared\[tunnel-id].json

   ingress:
     - hostname: api.yourdomain.com
       service: http://localhost:8000
     - service: http_status:404
   ```

5. **Create DNS record:**
   ```bash
   cloudflared tunnel route dns sasha-ai-backend api.yourdomain.com
   ```

6. **Run the tunnel:**
   ```bash
   cloudflared tunnel run sasha-ai-backend
   ```

### **Update CORS Settings**

Add your tunnel domain to `config/app_config.py`:
```python
CORS_ORIGINS = [
    "http://localhost:*",
    "https://your-frontend-domain.com",
    "https://api.yourdomain.com"  # Your tunnel endpoint
]
```

### **For Interviews/Demos**

1. Start backend: `python main.py`
2. Start tunnel: `cloudflared tunnel run sasha-ai-backend`
3. Share your frontend URL with interviewers
4. Your local backend is now accessible via `https://api.yourdomain.com`

**Benefits:**
- ✅ Professional HTTPS URLs
- ✅ No port forwarding needed
- ✅ Bypasses firewalls
- ✅ DDoS protection via Cloudflare
- ✅ Free and reliable
