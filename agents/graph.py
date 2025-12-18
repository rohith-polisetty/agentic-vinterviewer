from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage
import operator

from .resume_analyst import analyze_resume
from .interviewer import interviewer_node
from .evaluator import evaluator_node

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    candidate_profile: Dict[str, Any]
    interview_stage: str
    current_topic: str
    satisfaction_score: float
    code_output: str
    session_id: str
    resume_text: str

def route_interviewer(state):
    """
    Decide next step after interviewer.
    If the last message contains code, go to evaluator.
    Otherwise, continue interview or end.
    """
    messages = state["messages"]
    last_msg = messages[-1]
    
    # Check if user provided code
    if "```python" in last_msg.content or "```" in last_msg.content:
        # Only if it's a user message
        if isinstance(last_msg, HumanMessage): # Or check type if using dicts
             return "evaluator"
             
    # If stage is closure, end
    if state.get("interview_stage") == "closure":
        return END
        
    return END # For now, we just stop and wait for next user input in the Streamlit app loop
    # In a real continuous agent loop, we would return "interviewer" to keep generating, 
    # but here we want to stop and wait for user input. 
    # Actually, LangGraph is usually run until it hits a "wait for input" state or END.
    # Since we are integrating with Streamlit, we likely run one turn at a time.
    
    # However, for the purpose of this graph, let's define the flow:
    # User Input -> Interviewer -> (maybe Evaluator) -> End (wait for next input)

workflow = StateGraph(AgentState)

workflow.add_node("resume_analyst", analyze_resume)
workflow.add_node("interviewer", interviewer_node)
workflow.add_node("evaluator", evaluator_node)

# Entry point logic
workflow.set_entry_point("resume_analyst")

# Edges
workflow.add_edge("resume_analyst", "interviewer")

# Conditional edge from interviewer
# For this simple request-response model in Streamlit, we might not need complex looping *inside* the graph 
# for a single turn, unless we want the agent to self-correct.
# But let's support the code evaluation flow.
# If the user sends a message, we run the graph.
# If it's the FIRST run, we might go to resume_analyst.
# If it's a follow-up, we go to interviewer.

# We need a way to skip resume_analyst if profile exists.
# LangGraph entry point is static, but we can have a conditional entry or a router node.
# Let's make a "router" node as entry.

def router_node(state):
    return state

workflow.add_node("router", router_node)
workflow.set_entry_point("router")

def initial_route(state):
    if not state.get("candidate_profile"):
        return "resume_analyst"
    return "interviewer"

workflow.add_conditional_edges(
    "router",
    initial_route,
    {
        "resume_analyst": "resume_analyst",
        "interviewer": "interviewer"
    }
)

# From interviewer, we might go to evaluator if the USER's message (which triggered this) had code?
# Wait, the graph runs *after* user input.
# If user input has code -> Interviewer sees it -> decides to evaluate?
# Or we detect it before interviewer?
# Let's say: User Input -> Router -> Interviewer (generates response)
# If User Input had code, maybe we want Evaluator to run FIRST?
# Or Interviewer says "Let me run that" -> calls tool -> Evaluator.
# Given the architecture "Agent C: The Code Evaluator", it seems it should be a separate node.
# Let's keep it simple:
# If user input has code, we route to Evaluator first, then Interviewer comments on it?
# Or Interviewer runs, sees code, and calls Evaluator?
# Let's try: Router -> (if code) Evaluator -> Interviewer
#           Router -> (no code) Interviewer

def route_input(state):
    messages = state["messages"]
    
    # If no messages, check if we need to analyze resume
    if not messages:
        if not state.get("candidate_profile"):
            return "resume_analyst"
        return "interviewer"

    # The last message is the new user input
    last_msg = messages[-1]
    if isinstance(last_msg, HumanMessage) and ("```python" in last_msg.content or "def " in last_msg.content):
        return "evaluator"
    
    if not state.get("candidate_profile"):
        return "resume_analyst"
        
    return "interviewer"

# Redefine edges based on this logic
# We need to clear previous entry point if we are redefining, but since we are writing the file fresh:
workflow = StateGraph(AgentState)
workflow.add_node("resume_analyst", analyze_resume)
workflow.add_node("interviewer", interviewer_node)
workflow.add_node("evaluator", evaluator_node)

def start_router(state):
    # This is a dummy node just to make conditional routing easier from start
    return state

workflow.add_node("start_router", start_router)
workflow.set_entry_point("start_router")

workflow.add_conditional_edges(
    "start_router",
    route_input,
    {
        "evaluator": "evaluator",
        "resume_analyst": "resume_analyst",
        "interviewer": "interviewer"
    }
)

workflow.add_edge("resume_analyst", "interviewer")
workflow.add_edge("evaluator", "interviewer") # Evaluator passes result to interviewer to comment
workflow.add_edge("interviewer", END)

app_graph = workflow.compile()
