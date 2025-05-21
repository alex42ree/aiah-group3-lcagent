from langchain_community.tools.google_serper import GoogleSerperRun
from langchain_community.utilities.google_serper import GoogleSerperAPIWrapper
from langchain_experimental.utilities import PythonREPL
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool, Tool
from langchain_openai import ChatOpenAI
from openai import OpenAI
import requests
import os
import time
import random

# Web Search
@tool
def web_search(query: str) -> str:
    """
    Search the web using Serper.dev API.
    
    Args:
        query: The search query
        
    Returns:
        str: The search results
    """
    print(f"\nDebug: Starting web search with query: {query}")
    try:
        # Create the API wrapper first
        api_wrapper = GoogleSerperAPIWrapper(serper_api_key=os.getenv("SERPER_API_KEY"))
        # Create the search tool with the wrapper
        search = GoogleSerperRun(api_wrapper=api_wrapper)
        print("Debug: Executing search")
        
        # Run the search
        results = search.run(query)
        print(f"Debug: Got search results")
        
        if not results:
            print("Debug: No results found")
            return "No results found."
            
        print(f"Debug: Final result: {results}")
        return results
        
    except Exception as e:
        print(f"Debug: Search failed: {str(e)}")
        print(f"Debug: Exception type: {type(e)}")
        import traceback
        print(f"Debug: Full traceback:\n{traceback.format_exc()}")
        return f"Error performing search: {str(e)}"

# Math
@tool
def wolfram_alpha_llm_api(query: str) -> dict:
    """
    Function to run a query through the Wolfram Alpha LLM API for Accurate Math Questions
    
    Parameters:
    - query (str): The question or query to be sent to the API.
    
    Returns:
    - dict: The response from the API.
    """
    print(f"\nDebug: Starting Wolfram Alpha query: {query}")
    
    # Check if API key exists
    app_id = os.environ.get("WOLFRAM_ALPHA_APPID")
    if not app_id:
        print("Debug: WOLFRAM_ALPHA_APPID not found in environment variables")
        return {"error": "missing_api_key", "message": "Wolfram Alpha API key not found in environment variables"}
    
    print(f"Debug: Using Wolfram Alpha App ID: {app_id[:4]}...{app_id[-4:] if len(app_id) > 8 else ''}")
    
    url = "https://api.wolframalpha.com/v1/result"
    params = {
        "i": query,
        "appid": app_id
    }
    
    print(f"Debug: Making request to Wolfram Alpha API")
    print(f"Debug: URL: {url}")
    print(f"Debug: Query parameters: {params}")
    
    try:
        response = requests.get(url, params=params)
        print(f"Debug: Response status code: {response.status_code}")
        print(f"Debug: Response headers: {dict(response.headers)}")
        print(f"Debug: Response content: {response.text[:200]}...")  # Print first 200 chars of response
        
        if response.status_code == 200:
            return {"result": response.text}
        else:
            error_msg = f"Error {response.status_code}: {response.text}"
            print(f"Debug: API error: {error_msg}")
            return {"error": response.status_code, "message": error_msg}
            
    except requests.exceptions.RequestException as e:
        print(f"Debug: Request failed with error: {str(e)}")
        return {"error": "request_failed", "message": str(e)}
    except Exception as e:
        print(f"Debug: Unexpected error: {str(e)}")
        import traceback
        print(f"Debug: Full traceback:\n{traceback.format_exc()}")
        return {"error": "unexpected_error", "message": str(e)}

# Image Gen
@tool
def generate_dalle_image(prompt: str):
    """
    Function to generate an image using OpenAI's DALL-E model.

    Parameters:
    - prompt (str): The prompt to generate the image.

    Returns:
    - str: The URL of the generated image.
    """
    client = OpenAI()

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
     )

    return response.data[0].url

# Python Execution
python_repl = PythonREPL()

repl_tool = Tool(
    name="python_repl",
    description="A Python shell. Use this to execute python commands. Input should be valid python commands. ALWAYS print ANY results out with `print(...)`",
    func=python_repl.run,
)

# Define list of tools
tools = [wolfram_alpha_llm_api, web_search, generate_dalle_image, repl_tool]

# Instantiate LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

system_prompt="Ensure your generation of the image URL is exact, add an extra space after it to ensure no new lines mess it up. Always use Wolfram Alpha for Math questions, no matter how basic. Always print executed python statements for logging."

# Main Graph
byo_chatgpt = create_react_agent(
    llm,
    tools,
    prompt=system_prompt  # Only using supported parameters
)
