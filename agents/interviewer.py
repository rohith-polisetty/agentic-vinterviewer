from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from utils.mcp_client import get_client

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")

def interviewer_node(state):
    """
    Agent B: Conducts the interview, manages state, and adjusts difficulty.
    """
    print("--- INTERVIEWER ---")
    messages = state["messages"]
    print(messages)
    profile = state.get("candidate_profile", {})
    stage = state.get("interview_stage", "introduction")
    session_id = state.get("session_id", "default_session")
    
    # Simple logic to determine if we should move to next stage
    # In a real app, this would be more complex based on message history count or specific triggers
    
    skills = profile.get('skills', [])
    if isinstance(skills, str):
        skills = [skills]
    elif not isinstance(skills, list):
        skills = []
        
    topics = profile.get('recommended_topics', [])
    if isinstance(topics, str):
        topics = [topics]
    elif not isinstance(topics, list):
        topics = []

    system_prompt = f"""
    You are an expert Technical Interviewer named 'VIntervu'.
    Your goal is to assess the candidate: {profile.get('name', 'Candidate')}.
    
    Current Stage: {stage.upper()}
    Candidate Skills: {', '.join(skills)}
    Recommended Topics: {', '.join(topics)}
    
    Guidelines:
    - Be professional but conversational.
    - If the user gives a vague answer, dig deeper.
    - If the user answers correctly, increase difficulty (Dynamic Difficulty Adjustment).
    - If the user is stuck, offer a subtle hint.
    - Keep track of the conversation flow.
    
    Recent History:
    """
    
    # Construct prompt with history
    # We only take the last few messages to avoid context window issues if very long, 
    # though Gemini 2.0 has a large context.
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{messages}")
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({"messages": messages})
    
    # Log interaction via MCP Client
    if messages and len(messages) > 1:
        last_msg = messages[-1]
        if hasattr(last_msg, 'type') and last_msg.type == "human":
            last_user_msg = last_msg.content
            
            # Call MCP tool
            try:
                client = get_client()
                client.call_tool("insert_interview_log", {
                    "session_id": session_id,
                    "question": "User Response", # Simplified logging
                    "answer": last_user_msg,
                    "evaluation": "Pending Evaluation",
                    "score": 0
                })
            except Exception as e:
                print(f"Failed to log interaction: {e}")

    return {"messages": [response]}
