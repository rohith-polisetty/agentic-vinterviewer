from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import AIMessage
from utils.mcp_client import get_client

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")

def analyze_resume(state):
    """
    Agent A: Analyzes the resume and builds a candidate profile.
    """
    print("--- RESUME ANALYST ---")
    resume_text = state.get("resume_text", "")
    print(resume_text)
    if not resume_text:
        return {"messages": [AIMessage(content="Error: No resume text provided.")]}

    prompt = ChatPromptTemplate.from_template(
        """
        You are an expert Technical Recruiter and Resume Analyst.
        Analyze the following resume text and extract a structured candidate profile.
        
        Resume Text:
        {resume_text}
        
        Return a JSON object with the following fields:
        - name: Candidate's full name
        - skills: List of technical skills
        - experience_years: Estimated years of experience
        - roles: List of previous job titles
        - education: Highest degree and major
        - strengths: Key strengths identified
        - weaknesses: Potential gaps or areas to probe
        - recommended_topics: List of 3-5 technical topics to ask about based on their specific experience.
        
        Ensure the output is valid JSON.
        """
    )
    
    chain = prompt | llm | JsonOutputParser()
    
    try:
        profile = chain.invoke({"resume_text": resume_text})
        print(profile)
        
        if not profile or not isinstance(profile, dict):
            return {"messages": [AIMessage(content="Error: Failed to parse resume into a valid profile format.")]}
        
        # Save to DB via MCP Client
        client = get_client()
        # Note: We need to serialize arguments as a dict for call_tool
        # The tool signature is save_candidate_profile(name, resume_text, profile_json)
        # We need to pass profile as JSON string
        client.call_tool("save_candidate_profile", {
            "name": profile.get("name", "Unknown"),
            "resume_text": resume_text,
            "profile_json": json.dumps(profile)
        })
        
        return {
            "candidate_profile": profile,
            "interview_stage": "introduction",
            "messages": [AIMessage(content=f"Resume analyzed for {profile.get('name', 'Candidate')}. Ready to start interview.")]
        }
    except Exception as e:
        return {"messages": [AIMessage(content=f"Error analyzing resume: {str(e)}")]}
