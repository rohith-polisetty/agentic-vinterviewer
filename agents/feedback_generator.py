from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize LLM with API key
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

def feedback_generator_node(state):
    """
    Generates feedback for the last question-answer pair.
    Stores feedback in the state's feedbacks list.
    """
    print("--- FEEDBACK GENERATOR ---")
    messages = state["messages"]
    stage = state.get("interview_stage", "unknown")
    
    # Get last two messages (AI question, User answer)
    if len(messages) < 2:
        return {"feedbacks": []}
    
    last_ai_msg = None
    last_user_msg = None
    
    # Find the last AI and user messages
    for msg in reversed(messages):
        if hasattr(msg, 'type'):
            if msg.type == "ai" and last_ai_msg is None:
                last_ai_msg = msg.content
            elif msg.type == "human" and last_user_msg is None:
                last_user_msg = msg.content
        if last_ai_msg and last_user_msg:
            break
    
    if not last_ai_msg or not last_user_msg:
        return {"feedbacks": []}
    
    # Generate feedback using LLM
    feedback_prompt = ChatPromptTemplate.from_template(
        """
        You are an expert Technical Interviewer providing constructive feedback.
        
        Interview Stage: {stage}
        Question: {question}
        Candidate's Answer: {answer}
        
        Please provide:
        1. Brief feedback (2-3 sentences) on the answer quality
        2. A score from 1-10 based on:
           - Clarity and completeness
           - Technical accuracy
           - Depth of understanding
        
        Format your response as:
        **Feedback:** [Your feedback here]
        **Score:** [X/10]
        """
    )
    
    chain = feedback_prompt | llm
    result = chain.invoke({
        "stage": stage.upper(),
        "question": last_ai_msg,
        "answer": last_user_msg
    })
    
    feedback_text = result.content
    
    # Extract score from response
    score = 5  # Default
    if "Score:" in feedback_text or "score:" in feedback_text:
        try:
            score_part = feedback_text.split("Score:")[1].split("/")[0].strip()
            score = int(score_part.replace("*", "").strip())
        except:
            score = 5
    
    feedback_entry = {
        "question": last_ai_msg,
        "answer": last_user_msg,
        "feedback": feedback_text,
        "score": score,
        "stage": stage
    }
    
    return {"feedbacks": [feedback_entry]}


def final_feedback_node(state):
    """
    Aggregates all feedbacks and provides comprehensive final evaluation.
    """
    print("--- FINAL FEEDBACK ---")
    feedbacks = state.get("feedbacks", [])
    candidate_profile = state.get("candidate_profile", {})
    
    if not feedbacks:
        return {
            "messages": [AIMessage(content="No feedback available to generate final evaluation.")],
            "interview_stage": "completed"
        }
    
    # Calculate average score
    total_score = sum(f.get("score", 0) for f in feedbacks)
    avg_score = total_score / len(feedbacks) if feedbacks else 0
    
    # Group feedbacks by stage
    stage_feedbacks = {
        "self_intro": [],
        "technical": [],
        "dsa": []
    }
    
    for fb in feedbacks:
        stage = fb.get("stage", "unknown")
        if stage in stage_feedbacks:
            stage_feedbacks[stage].append(fb)
    
    # Generate comprehensive feedback
    final_prompt = ChatPromptTemplate.from_template(
        """
        You are an expert Technical Interviewer providing a comprehensive final evaluation.
        
        Candidate: {candidate_name}
        Total Questions: {total_questions}
        Average Score: {avg_score:.1f}/10
        
        Individual Feedbacks:
        {feedback_summary}
        
        Please provide a comprehensive final evaluation with:
        1. **Overall Performance Summary** - High-level assessment
        2. **Strengths** - Key strong points demonstrated
        3. **Areas for Improvement** - Specific suggestions
        4. **Stage-wise Analysis**:
           - Self Introduction: Brief comments
           - Technical Questions: Brief comments
           - DSA/Coding: Brief comments (if applicable)
        5. **Final Rating** - Overall score out of 10 and recommendation
        
        Be constructive, specific, and professional. Format in clear markdown.
        """
    )
    
    # Build feedback summary
    feedback_summary = ""
    for i, fb in enumerate(feedbacks, 1):
        feedback_summary += f"\n{i}. [{fb['stage'].upper()}] Score: {fb['score']}/10\n"
        feedback_summary += f"   Q: {fb['question'][:100]}...\n"
        feedback_summary += f"   A: {fb['answer'][:100]}...\n"
        feedback_summary += f"   Feedback: {fb['feedback'][:150]}...\n"
    
    chain = final_prompt | llm
    result = chain.invoke({
        "candidate_name": candidate_profile.get("name", "Candidate"),
        "total_questions": len(feedbacks),
        "avg_score": avg_score,
        "feedback_summary": feedback_summary
    })
    
    final_feedback_text = result.content
    
    # Store final score in state
    final_score = {
        "overall_score": round(avg_score, 1),
        "total_questions": len(feedbacks),
        "stage_scores": {
            "self_intro": round(sum(f["score"] for f in stage_feedbacks["self_intro"]) / len(stage_feedbacks["self_intro"]), 1) if stage_feedbacks["self_intro"] else 0,
            "technical": round(sum(f["score"] for f in stage_feedbacks["technical"]) / len(stage_feedbacks["technical"]), 1) if stage_feedbacks["technical"] else 0,
            "dsa": round(sum(f["score"] for f in stage_feedbacks["dsa"]) / len(stage_feedbacks["dsa"]), 1) if stage_feedbacks["dsa"] else 0
        }
    }
    
    return {
        "messages": [AIMessage(content=final_feedback_text)],
        "final_score": final_score,
        "interview_stage": "completed"
    }
