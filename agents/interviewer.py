from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)


def self_intro_node(state):
    print("--- SELF INTRO ---")
    messages = state["messages"]


    if state.get("interview_stage") != "self_intro":
        return {}


    if not messages:
        return {
            "messages": [AIMessage(content=(
                "Welcome to VIntervu!\n\n"
                "Please introduce yourself:\n"
                "- Background\n"
                "- Experience\n"
                "- Skills\n"
                "- Key projects"
            ))],
            "interview_stage": "self_intro",
            "questions_asked": 0
        }

    last_msg = messages[-1]
    if last_msg.type != "human":
        return {}

    intro_text = last_msg.content

    prompt = ChatPromptTemplate.from_template(
        """
        Extract:
        - Skills
        - Experience
        - Projects
        - Domains

        From:
        {intro}

        Return JSON.
        """
    )

    profile = (prompt | llm).invoke({"intro": intro_text})

    return {
        "candidate_profile": {
            "raw_intro": intro_text,
            "summary": profile.content
        },
        "messages": [AIMessage(content="Thanks! Let’s begin the technical interview.")],
        "interview_stage": "technical",
        "questions_asked": 0
    }


def technical_questions_node(state):
    print("--- TECHNICAL QUESTION ASKER ---")
    messages = state["messages"]

    # 🚨 CRITICAL GUARD
    if messages and messages[-1].type == "human":
        return {}

    questions_asked = state.get("questions_asked", 0)
    profile = state.get("candidate_profile", {})

    if questions_asked >= 10:
        return {
            "interview_stage": "dsa",
            "questions_asked": 0,
            "messages": [AIMessage(content="Great. Let’s move to DSA questions.")]
        }

    system_prompt = f"""
    You are a technical interviewer.

    Candidate profile:
    {profile}

    Ask ONE deep technical question
    based on their skills or projects.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt)
    ])

    question = (prompt | llm).invoke({})

    return {
        "messages": [question],
        "questions_asked": questions_asked + 1
    }


def ambiguity_checker_node(state):
    print("--- AMBIGUITY CHECKER ---")
    messages = state["messages"]

    last_user = next(
        (m.content for m in reversed(messages) if m.type == "human"),
        None
    )

    if not last_user:
        return {"ambiguity_detected": False}

    prompt = ChatPromptTemplate.from_template(
        """
        Answer:
        {answer}

        Is this vague or shallow?
        Reply ONLY YES or NO.
        """
    )

    result = (prompt | llm).invoke({"answer": last_user})
    ambiguous = "YES" in result.content.upper()

    if ambiguous:
        followup_prompt = ChatPromptTemplate.from_template(
            """
            Candidate said:
            {answer}

            Ask ONE deeper follow-up question
            requiring implementation details.
            """
        )

        followup = (followup_prompt | llm).invoke({"answer": last_user})

        return {
            "messages": [AIMessage(content=followup.content)],
            "ambiguity_detected": True,
            "feedbacks": [{
                "type": "clarity",
                "comment": "Answer lacked depth or specifics"
            }]
        }

    return {"ambiguity_detected": False}


def dsa_questions_node(state):
    print("--- DSA QUESTIONS ---")
    messages = state["messages"]

    if messages and messages[-1].type == "human":
        return {}

    questions_asked = state.get("questions_asked", 0)

    if questions_asked >= 2:
        return {
            "interview_stage": "final_feedback",
            "messages": [AIMessage(content="Thanks! Preparing final feedback.")]
        }

    prompt = ChatPromptTemplate.from_template(
        """
        Ask ONE medium-level DSA problem.
        Include:
        - Problem
        - Example
        - Constraints
        """
    )

    question = (prompt | llm).invoke({})

    return {
        "messages": [question],
        "questions_asked": questions_asked + 1
    }
