from typing import TypedDict, List, Dict, Any, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import BaseMessage
import operator
import os

from .interviewer import (
    self_intro_node,
    technical_questions_node,
    ambiguity_checker_node,
    dsa_questions_node
)
from .feedback_generator import feedback_generator_node, final_feedback_node
from .resume_analyst import analyze_resume
from .evaluator import  evaluator_node


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    feedbacks: Annotated[List[Dict[str, Any]], operator.add]
    candidate_profile: Dict[str, Any]
    interview_stage: str
    questions_asked: int
    ambiguity_detected: bool
    session_id: str
    resume_text: str


def route_after_self_intro(state):
    return "technical_questions" if state.get("interview_stage") == "technical" else "self_intro"


def route_after_technical(state):
    messages = state["messages"]

    if not messages:
        return END

    if messages[-1].type == "human":
        return "ambiguity_checker"

    return END


def route_after_ambiguity(state):
    if state.get("ambiguity_detected"):
        return END
    return "technical_feedback"


def route_after_feedback(state):
    stage = state.get("interview_stage")

    if stage == "technical":
        return "technical_questions"
    if stage == "dsa":
        return "dsa_questions"
    if stage == "final_feedback":
        return "final_feedback"

    return END


def route_after_dsa(state):
    messages = state["messages"]

    if messages and messages[-1].type == "human":
        return "code_evaluator"

    return END


workflow = StateGraph(AgentState)

workflow.add_node("resume_analyst", analyze_resume)
workflow.add_node("self_intro", self_intro_node)
workflow.add_node("technical_questions", technical_questions_node)
workflow.add_node("ambiguity_checker", ambiguity_checker_node)
workflow.add_node("technical_feedback", feedback_generator_node)
workflow.add_node("dsa_questions", dsa_questions_node)
workflow.add_node("code_evaluator", evaluator_node)
workflow.add_node("final_feedback", final_feedback_node)

workflow.set_entry_point("resume_analyst")

workflow.add_edge("resume_analyst", "self_intro")

workflow.add_conditional_edges(
    "self_intro",
    route_after_self_intro,
    {
        "self_intro": "self_intro",
        "technical_questions": "technical_questions"
    }
)

workflow.add_conditional_edges(
    "technical_questions",
    route_after_technical,
    {
        "ambiguity_checker": "ambiguity_checker",
        END: END
    }
)

workflow.add_conditional_edges(
    "ambiguity_checker",
    route_after_ambiguity,
    {
        "technical_feedback": "technical_feedback",
        END: END
    }
)

workflow.add_conditional_edges(
    "technical_feedback",
    route_after_feedback,
    {
        "technical_questions": "technical_questions",
        "dsa_questions": "dsa_questions",
        "final_feedback": "final_feedback",
        END: END
    }
)

workflow.add_conditional_edges(
    "dsa_questions",
    route_after_dsa,
    {
        "code_evaluator": "code_evaluator",
        END: END
    }
)

workflow.add_edge("final_feedback", END)

checkpoint_dir = os.path.join(os.path.dirname(__file__), "checkpoints")
os.makedirs(checkpoint_dir, exist_ok=True)

memory = SqliteSaver.from_conn_string(
    os.path.join(checkpoint_dir, "vintervu.db")
)

app_graph = workflow.compile(checkpointer=memory)
