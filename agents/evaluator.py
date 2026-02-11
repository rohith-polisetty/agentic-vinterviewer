import sys
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")

def evaluator_node(state):
    """
    Agent C: Verifies coding answers by using LLM to simulate and evaluate.
    """
    print("--- CODE EVALUATOR (LLM) ---")
    messages = state["messages"]
    last_message = messages[-1]
    
    # Extract code from the last message (assuming markdown code blocks)
    content = last_message.content
    code_block = ""
    if "```python" in content:
        code_block = content.split("```python")[1].split("```")[0].strip()
    elif "```" in content:
        code_block = content.split("```")[1].split("```")[0].strip()
        
    if not code_block:
        return {"messages": [AIMessage(content="I didn't detect any code to run. Please provide your solution in a Python code block.")]}
    
    # Evaluate using LLM (Simulation + Feedback)
    eval_prompt = ChatPromptTemplate.from_template(
        """
        You are an expert Python Code Evaluator.
        
        User Code:
        ```python
        {code}
        ```
        
        Please perform the following:
        1. **Simulate Execution**: Predict exactly what this code would output if run.
        2. **Evaluation**: Is the code correct, efficient, and following best practices?
        
        Format your response as:
        **Predicted Output:**
        ```
        [Output here]
        ```
        
        **Feedback:**
        [Your detailed feedback here]
        """
    )
    
    chain = eval_prompt | llm
    result = chain.invoke({"code": code_block})
    
    # We treat the whole LLM response as the "output" for the user to see
    return {
        "code_output": "LLM Simulated Execution", # Placeholder for state
        "messages": [AIMessage(content=result.content)]
    }
