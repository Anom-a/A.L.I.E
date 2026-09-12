# A.L.I.E. (Automated Learning and Intelligence Engine)

A.L.I.E. is an agentic research assistant that can take a query, break it down into sub-questions, autonomously search the web or specific sources for evidence, and synthesize a fully cited final report. 

This repository is split into two main parts:
- **`backend/`**: A Python FastAPI application that runs the research pipeline (Planner -> Router -> Retrieval -> Critic -> Synthesizer) using LangGraph.
- **`frontend/`**: A React + Vite application that provides a modern, interactive chat UI to start research queries and view the generated reports.

## Prerequisites

- Node.js (v18+)
- Python 3.12+
- A [Tavily](https://tavily.com/) API Key for web search
- A working LLM Proxy or API Key for OpenAI-compatible structured generation

---

## 🚀 Running the Backend

The backend is built with FastAPI and runs inside a Python virtual environment.

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment** (if not already done):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *(If `requirements.txt` is not present, you can install the required packages like `fastapi`, `langgraph`, `tavily-python`, `openai`, `python-dotenv`, etc.)*

4. **Configure Environment Variables**:
   Copy the example environment file and fill in your keys:
   ```bash
   cp .env.example .env
   ```
   Make sure you set your API keys correctly inside `.env`:
   - `OPENAI_API_KEY`: Your LLM proxy API key or OpenAI key
   - `OPENAI_BASE_URL`: The base URL of your LLM provider (e.g. `http://localhost:3001/v1/`)
   - `TAVILY_API_KEY`: Your Tavily Search API key
   - `REQUEST_TIMEOUT_SECONDS`: Set this to `120` to give the synthesizer enough time to generate the report.

5. **Start the FastAPI server**:
   ```bash
   fastapi dev infrastructure/api/main.py
   ```
   The backend will start and listen on `http://127.0.0.1:8000`.

---

## 💻 Running the Frontend

The frontend is a React application powered by Vite.

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```
   The Vite server will start on `http://localhost:3000`. 

## 🧪 Testing the Application

Once both the frontend and backend are running:
1. Open your browser and navigate to `http://localhost:3000`.
2. Type a research query in the chat window (e.g., "I want to change my screen for my galaxy a15").
3. Click "Start Research".
4. You will see the pipeline progress from "Pending" to "Running" and finally "Done", where it will display a fully cited Markdown report!
