# semantic-ai-assistant
This system is a Voice-based AI Query Optimization Platform that reduces expensive LLM API calls by using semantic caching (embeddings + similarity search) and provides real-time responses using a fallback AI model when needed


🤖 Voice AI Query Optimization System

A voice-enabled AI assistant platform that optimizes expensive LLM API usage by implementing semantic caching using embeddings and vector similarity search. The system reuses previously answered queries when possible and falls back to AI models only when necessary.


🚀 Key Features
🎤 Voice-based question input (browser speech recognition)
🧠 AI-powered responses using LLM APIs
⚡ Semantic caching using embeddings
🔍 Vector similarity search for duplicate question detection
💰 Reduced API cost by avoiding redundant AI calls
🗄️ Persistent storage of Q&A history
🔁 Smart fallback mechanism (cache → AI → store)

System Architecture 

User clicks  button
        ↓
Browser Speech Recognition API
        ↓
Converts Speech → Text
        ↓
Frontend (React / UI Layer)
        ↓
Backend API (FastAPI / Node.js)
        ↓
Processes Input (Logic / AI / DB)
        ↓
Returns Response
        ↓
UI Displays Answer

Architecture Diagram

<img width="498" height="744" alt="image" src="https://github.com/user-attachments/assets/7b538e08-adc5-4c48-a90e-85352e68f8b5" />


Tech Stack
Frontend
React.js
Web Speech API (Speech-to-Text)
Backend
FastAPI (Python)
Uvicorn server
Database
PostgreSQL
SQLite
pgvector extension (for embeddings)
AI / ML
OpenAI (Embeddings + Response generation)
or Anthropic
