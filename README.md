# SF Hacks Mental Health Chatbot

This project is a mental health chatbot built using the Gemini API with RAG (Retrieval-Augmented Generation) enhancement using ChromaDB.

## Getting Started

1. **Prerequisites:**
   - Python 3.x is installed on your system.
   - pip is installed (usually comes with Python).

2. **Clone the Repository:**
   ```bash
   git clone [repository URL]
   cd sfhacks-mental-health-chatbot
   ```

## Backend Setup

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   
   # On macOS and Linux
   source venv/bin/activate
   
   # On Windows
   .\venv\Scripts\activate
   ```

2. **Install requirements:**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Set up your .env file:**
   - Copy the `.env.example` file to `.env` in the backend directory
   - Add your Google Gemini API key

4. **ChromaDB Setup:**
   - The application will automatically set up a local ChromaDB instance
   - Data will be stored in the `./chroma_db` directory
   - The first time you run the application, it will download the mental health conversations dataset and create embeddings
   - Rate limiting is implemented to avoid Google API quota issues
   - Only 100 samples are initially processed to ensure quick startup

## Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the React development server:**
   ```bash
   npm start
   ```

## Running the Application

1. **Start the backend server:**
   ```bash
   cd backend
   python app.py
   ```
   The backend will automatically initialize the RAG database on first run.

2. **Open the frontend in your browser:**
   - Navigate to `http://localhost:3000` to interact with the chatbot.

## Features

- Mental health chatbot using Gemini 2.0 Flash
- Specialized response routing based on mental health topics
- RAG enhancement using the mental_health_counseling_conversations dataset
- Vector search through ChromaDB for semantic similarity
- Persistent vector database storage for conversation examples