# Building a Custom AI for Sasha — ELI5 Guide

> **ELI5 = Explain Like I'm 5.** This guide explains how to replace Ollama with your own trained AI model, in plain English, step by step. No PhD required.

---

## The Big Picture (What We're Actually Doing)

Right now, Sasha uses **Ollama** — think of it like hiring a really smart contractor who already knows how to talk. You just hand them a note that says "here's what you know about Erin" and they do the rest.

The goal is to eventually **train your own employee from scratch** — someone who has read everything about Erin so many times that they just *know* it, without needing the note every time.

That process is called **fine-tuning** a language model.

---

## Step 1 — Understand What "Training" Actually Means

Imagine you're teaching a parrot to answer questions about you.

- You say: *"What do I do for work?"* → parrot hears it 500 times → eventually it just knows the answer
- That's training. You show the model thousands of examples of questions and correct answers, and it learns the pattern.

In AI terms:
- **Base model** = the parrot that already knows how to talk (just not about you)
- **Fine-tuning** = showing it your specific Q&A pairs until it learns your answers
- **Training data** = the list of Q&A pairs you feed it

---

## Step 2 — Pick a Base Model

You don't build a language model from absolute zero — that takes millions of dollars and Google-scale hardware. Instead, you start with a small open-source model that already knows how to speak English, and you *fine-tune* it on your data.

Good options for a home PC (no GPU required, or small GPU):

| Model | Size | Good For |
|-------|------|----------|
| `TinyLlama-1.1B` | ~600MB | Very fast, low RAM, good for testing |
| `Phi-3-mini` | ~2GB | Smart for its size, Microsoft-made |
| `Mistral-7B` | ~4GB | Best quality, needs more RAM (~8GB) |
| `Llama-3.2-3B` | ~2GB | Good balance of quality and speed |

**Recommendation to start:** `Phi-3-mini` or `TinyLlama` — they run fine on a regular PC with 8–16GB RAM.

---

## Step 3 — Collect Training Data

This is the most important step. The model is only as good as the data you feed it.

You need a file of Q&A pairs written in Erin's voice. Format:

```json
[
  {
    "instruction": "What do you do for work?",
    "response": "Erin is a Full-Stack Engineer currently at Payactiv, where she led the architecture of a React Native + Next.js monorepo supporting three production apps."
  },
  {
    "instruction": "What's your tech stack?",
    "response": "Erin works across the full stack — TypeScript, React, Next.js, and React Native on the front end, and Python, Node.js, and C# on the back end. She's also comfortable with AWS, SQLite, PostgreSQL, and MongoDB."
  }
]
```

**Where to get training data:**
1. **Write it manually** — 200–500 Q&A pairs is a good start. Cover: work history, tech stack, projects, personality, opinions, hobbies, fun facts
2. **Export from the knowledge DB** — every approved knowledge entry can become a training example
3. **Mine the MISC category** — real questions visitors asked Sasha, with Sasha's answers = real training signal

Save this as `backend/data/training_data.json`.

---

## Step 4 — Fine-Tune the Model

This is where the actual "training" happens. You'll use two Python libraries:

- **`transformers`** — Hugging Face's library for loading and running models
- **`trl`** — a library specifically for fine-tuning chat models (SFTTrainer)

### Install dependencies

```bash
pip install transformers trl datasets torch accelerate peft bitsandbytes
```

### Fine-tuning script (save as `backend/scripts/train.py`)

```python
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import SFTTrainer
import json

# Load your training data
with open("data/training_data.json") as f:
    raw = json.load(f)

# Format as chat-style text
def format_example(ex):
    return f"### Question:\n{ex['instruction']}\n\n### Answer:\n{ex['response']}"

data = Dataset.from_list([{"text": format_example(ex)} for ex in raw])

# Load the base model
model_name = "microsoft/phi-3-mini-4k-instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Training settings
args = TrainingArguments(
    output_dir="./sasha-model",
    num_train_epochs=3,           # How many times to read the whole dataset
    per_device_train_batch_size=2,
    save_steps=100,
    logging_steps=10,
    learning_rate=2e-4,
    fp16=False,                   # Set True if you have a GPU
)

trainer = SFTTrainer(
    model=model,
    args=args,
    train_dataset=data,
    dataset_text_field="text",
    max_seq_length=512,
)

trainer.train()
trainer.save_model("./sasha-model/final")
print("Training complete! Model saved to ./sasha-model/final")
```

### Run it

```bash
cd backend
python scripts/train.py
```

This will take **30 minutes to several hours** depending on your PC and dataset size. It's normal for it to be slow.

---

## Step 5 — Test the Model

After training, test it before swapping it into the backend:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained("./sasha-model/final")
tokenizer = AutoTokenizer.from_pretrained("./sasha-model/final")

prompt = "### Question:\nWhat does Erin do for work?\n\n### Answer:\n"
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=200)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

Does it sound like Sasha? Does it answer correctly? If not, you need more/better training data and another round of training.

---

## Step 6 — Swap Into the Backend

Once the model is good, replace the Ollama API call in `backend/lib/model_manager.py` with local inference:

```python
# Replace the Ollama API call with this:
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class ModelManager:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("./sasha-model/final")
        self.model = AutoModelForCausalLM.from_pretrained("./sasha-model/final")

    def generate_response(self, message: str, conversation_history=None) -> str:
        prompt = f"### Question:\n{message}\n\n### Answer:\n"
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(**inputs, max_new_tokens=300, temperature=0.8)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True).split("### Answer:\n")[-1].strip()
```

The `/chat` endpoint, frontend, and Discord bot stay exactly the same — only the model changes.

---

## Step 7 — Make It Smaller (Optional but Recommended)

A 7B model takes ~14GB of RAM. You can shrink it using **quantization** — compressing the model with a tiny quality tradeoff:

```bash
pip install llama-cpp-python
# Convert to GGUF format (4-bit quantized = ~4GB instead of 14GB)
python -m llama_cpp.convert ./sasha-model/final --outtype q4_k_m --outfile sasha-q4.gguf
```

Then load it with `llama-cpp-python` instead of `transformers`. Much faster, much less RAM.

---

## Realistic Timeline

| Phase | Time Estimate |
|-------|--------------|
| Write 200 Q&A pairs | 2–4 hours |
| Set up training environment | 1 hour |
| First training run (TinyLlama, 200 examples) | 20–40 min |
| Evaluate + iterate | Ongoing |
| Swap into backend | 1–2 hours |

---

## Common Questions

**Do I need a GPU?**
No, but it's much faster with one. CPU-only training on TinyLlama with 200 examples takes ~30–60 minutes. On a GPU it's 5–10 minutes.

**Will it be as smart as Ollama?**
Not at first. The base Ollama model (`qwen2.5-coder:7b`) is very capable. Your fine-tuned model will be *more Erin-specific* but may be less fluent on general questions. That's the tradeoff — and why you keep iterating.

**What if the training makes it worse?**
Keep the Ollama version running. Only swap when you're happy with the fine-tuned version. You can always roll back.

**How do I keep it learning over time?**
Every time a new knowledge entry is approved via Discord, add it to `training_data.json` and run another fine-tuning pass. This is called **continual learning** and is Phase 5 in the TODO.

---

## Files You'll Create

```
backend/
├── data/
│   └── training_data.json     # Your Q&A pairs
├── scripts/
│   └── train.py               # Fine-tuning script
└── sasha-model/
    └── final/                 # Trained model output
```

---

> **TL;DR:** Write Q&A pairs → run the training script → test it → swap it in. The hard part is writing good training data, not the code.
