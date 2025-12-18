from mcp.server.fastmcp import FastMCP
import sqlite3
import json
from .database import get_db_connection, save_candidate, log_interaction, init_db

# Initialize database
init_db()

# Create MCP Server
mcp = FastMCP("VIntervu MCP Server")

@mcp.tool()
def query_db(sql_query: str) -> str:
    """
    Safe read-only access to the SQLite database.
    Use this to retrieve interview history, candidate details, or session status.
    """
    # Basic safety check to prevent modification
    if not sql_query.strip().lower().startswith("select"):
        return "Error: Only SELECT queries are allowed."
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Database Error: {str(e)}"

@mcp.tool()
def insert_interview_log(session_id: str, question: str, answer: str, evaluation: str, score: int) -> str:
    """
    Log an interview interaction (question, answer, evaluation, score) to the database.
    """
    try:
        log_interaction(session_id, question, answer, evaluation, score)
        return "Interaction logged successfully."
    except Exception as e:
        return f"Error logging interaction: {str(e)}"

@mcp.tool()
def fetch_job_market_data(role: str) -> str:
    """
    Returns 'current hot topics' for a specific role.
    Simulates fetching real-time market data.
    """
    role = role.lower()
    if "python" in role:
        return "Hot Topics: FastAPI, AsyncIO, Pydantic, Type Hinting, Microservices patterns."
    elif "frontend" in role or "react" in role:
        return "Hot Topics: React Server Components, Next.js 14, Tailwind CSS, State Management (Zustand/Jotai)."
    elif "data" in role:
        return "Hot Topics: Vector Databases, LLM Orchestration, Spark, dbt, Data Governance."
    else:
        return "Hot Topics: Cloud Native (Kubernetes), CI/CD pipelines, System Design, Security best practices."

@mcp.tool()
def save_candidate_profile(name: str, resume_text: str, profile_json: str) -> str:
    """
    Saves a parsed candidate profile to the database.
    profile_json should be a valid JSON string.
    """
    try:
        profile_data = json.loads(profile_json)
        candidate_id = save_candidate(name, resume_text, profile_data)
        return f"Candidate saved successfully. ID: {candidate_id}"
    except json.JSONDecodeError:
        return "Error: profile_json must be a valid JSON string."
    except Exception as e:
        return f"Error saving candidate: {str(e)}"

if __name__ == "__main__":
    mcp.run()
