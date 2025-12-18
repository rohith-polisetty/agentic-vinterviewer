# VIntervu 2.0 - Agentic AI Interviewer

VIntervu 2.0 is a state-of-the-art **Agentic AI System** designed to conduct autonomous technical interviews. It orchestrates multiple AI agents to analyze resumes, conduct adaptive interviews, and evaluate coding solutions in real-time.

Built with **LangGraph**, **Google Gemini 2.0 Flash**, **FastAPI**, **Streamlit**, and the **Model Context Protocol (MCP)**.

## 🚀 Features

*   **Multi-Agent Architecture**:
    *   **Resume Analyst**: Parses PDF/TXT resumes, extracts skills, and builds a candidate profile.
    *   **Interviewer**: Conducts the chat, adapts difficulty based on responses (Dynamic Difficulty Adjustment), and manages interview stages.
    *   **Code Evaluator**: Simulates code execution and provides detailed feedback on correctness and efficiency using LLMs.
*   **Decoupled Design**:
    *   **Backend**: FastAPI server hosting the LangGraph workflow and MCP client.
    *   **Frontend**: Streamlit UI for a seamless, interactive chat experience.
*   **Model Context Protocol (MCP)**:
    *   Uses MCP to standardize tool usage (Database interactions, Logging) via a JSON-RPC subprocess.
*   **Persistent State**: SQLite database stores candidate profiles, session logs, and interview history.

## 🛠️ Tech Stack

*   **Orchestration**: [LangGraph](https://langchain-ai.github.io/langgraph/)
*   **LLM**: Google Gemini 2.0 Flash (via `langchain-google-genai`)
*   **Backend**: FastAPI, Uvicorn
*   **Frontend**: Streamlit, Streamlit-Ace (Code Editor)
*   **Protocol**: Model Context Protocol (MCP) Python SDK
*   **Database**: SQLite

## 📂 Project Structure

```
VIntervu-2.0/
├── agents/                 # AI Agent Definitions
│   ├── resume_analyst.py   # Agent A: Profile Extraction
│   ├── interviewer.py      # Agent B: Interview Logic
│   ├── evaluator.py        # Agent C: Code Verification
│   └── graph.py            # LangGraph State Machine
├── backend/
│   └── main.py             # FastAPI Server & Entry Point
├── frontend/
│   └── app.py              # Streamlit User Interface
├── mcp_server/             # MCP Tool Definitions
│   ├── server.py           # MCP Server (JSON-RPC)
│   └── database.py         # SQLite Helpers
├── utils/
│   └── mcp_client.py       # MCP Client (Subprocess Manager)
├── requirements.txt        # Python Dependencies
└── .env                    # Configuration Secrets
```

## ⚡ Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd VIntervu-2.0
    ```

2.  **Create a Virtual Environment** (Recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**:
    Create a `.env` file in the root directory and add your Google API Key:
    ```env
    GOOGLE_API_KEY=your_gemini_api_key_here
    ```

## 🏃‍♂️ Usage

The application requires two separate terminal processes to run (Backend and Frontend).

### 1. Start the Backend (FastAPI)
This process hosts the agents and the MCP server.
```bash
python backend/main.py
```
*Server will start at `http://localhost:8000`*

### 2. Start the Frontend (Streamlit)
This process runs the user interface.
```bash
streamlit run frontend/app.py
```
*UI will open at `http://localhost:8501`*

## 📝 How to Use

1.  **Upload Resume**: On the sidebar, upload a PDF or TXT resume.
2.  **Analysis**: The **Resume Analyst** agent will process the file and generate a candidate profile.
3.  **Interview**: The **Interviewer** agent will start the conversation based on your skills.
4.  **Code Challenge**: When asked to write code, toggle the **"Open Code Editor"** checkbox, write your Python solution, and submit.
5.  **Feedback**: The **Evaluator** agent will review your code and provide feedback.

## 🤝 Contributing

1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.
