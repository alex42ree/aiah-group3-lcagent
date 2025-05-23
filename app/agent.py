from langchain_community.tools.google_serper import GoogleSerperRun
from langchain_community.utilities.google_serper import GoogleSerperAPIWrapper
from langchain_experimental.utilities import PythonREPL
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool, Tool, BaseTool
from langchain_openai import ChatOpenAI
from openai import OpenAI
from app.port_tools import PortExtractorTool
import requests
import os
import time
import random
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Debug: Print environment variables (masked for security)
print("\nDebug: Environment Variables:")
print(f"SERPER_API_KEY exists: {'Yes' if os.getenv('SERPER_API_KEY') else 'No'}")
print(f"SERPER_API_KEY length: {len(os.getenv('SERPER_API_KEY', '')) if os.getenv('SERPER_API_KEY') else 0}")
print(f"OPENAI_API_KEY exists: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
print(f"WOLFRAM_ALPHA_APPID exists: {'Yes' if os.getenv('WOLFRAM_ALPHA_APPID') else 'No'}")
print(f"API_URL: {os.getenv('API_URL', 'Not set')}\n")

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
        # Debug: Print API key status before creating wrapper
        print(f"Debug: SERPER_API_KEY exists before wrapper creation: {'Yes' if os.getenv('SERPER_API_KEY') else 'No'}")
        
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

class CountryDataInput(BaseModel):
    """Input for the country data tool."""
    operation: str = Field(description="The operation to perform: 'get_entry', 'search', or 'same_country'")
    entry_id: Optional[str] = Field(default=None, description="The ID of the entry to get")
    search_query: Optional[str] = Field(default=None, description="The search query for finding entries")
    entry1_id: Optional[str] = Field(default=None, description="First entry ID for same_country check")
    entry2_id: Optional[str] = Field(default=None, description="Second entry ID for same_country check")

class CountryDataTool(BaseTool):
    """Tool for managing and querying country-related data."""
    
    name: str = "country_data"
    description: str = """Use this tool to:
    1. Get a single entry by ID (e.g., 'DE-HAM', 'US-NYC', 'GB-LON')
    2. Search for entries by name or country
    3. Check if two entries are from the same country
    
    Operations:
    - get_entry: Get a single entry by its exact ID (e.g., 'DE-HAM' for Hamburg)
    - search: Search for entries by name or country (e.g., 'Hamburg' or 'Germany')
    - same_country: Check if two entries are from the same country
    
    When you have an exact ID (like 'DE-HAM'), always use get_entry operation."""
    
    args_schema: type[BaseModel] = CountryDataInput
    
    def _run(
        self,
        operation: str,
        entry_id: Optional[str] = None,
        search_query: Optional[str] = None,
        entry1_id: Optional[str] = None,
        entry2_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute the requested country data operation.
        
        Args:
            operation: The operation to perform
            entry_id: ID for get_entry operation (e.g., 'DE-HAM')
            search_query: Query for search operation (e.g., 'Hamburg')
            entry1_id: First entry ID for same_country check
            entry2_id: Second entry ID for same_country check
            
        Returns:
            Dictionary containing the operation result
        """
        try:
            # Get API URL from environment
            api_url = os.getenv('API_URL', 'http://localhost:3000')
            
            # If we have an entry_id that looks like a code (e.g., 'DE-HAM'), use get_entry
            if entry_id and '-' in entry_id:
                operation = 'get_entry'
            
            # Prepare request payload based on operation
            payload = {"operation": operation}
            
            if operation == "get_entry":
                if not entry_id:
                    return {"error": "entry_id is required for get_entry operation"}
                payload["entry_id"] = entry_id
            elif operation == "search":
                if not search_query:
                    return {"error": "search_query is required for search operation"}
                payload["search_query"] = search_query
            elif operation == "same_country":
                if not entry1_id or not entry2_id:
                    return {"error": "Both entry1_id and entry2_id are required for same_country operation"}
                payload["entry1_id"] = entry1_id
                payload["entry2_id"] = entry2_id
            
            print(f"Debug: Sending request to API with payload: {payload}")
            
            # Call the API endpoint
            response = requests.post(
                f"{api_url}/country-data",
                json=payload
            )
            
            if response.status_code != 200:
                return {
                    "error": f"API request failed with status {response.status_code}",
                    "details": response.text
                }
                
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                "error": "Request failed",
                "details": str(e)
            }
        except Exception as e:
            return {
                "error": "Unexpected error",
                "details": str(e)
            }
    
    async def _arun(
        self,
        operation: str,
        entry_id: Optional[str] = None,
        search_query: Optional[str] = None,
        entry1_id: Optional[str] = None,
        entry2_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Async implementation of the country data operations."""
        return self._run(operation, entry_id, search_query, entry1_id, entry2_id)

# Define list of tools
tools = [
    wolfram_alpha_llm_api,
    web_search,
    generate_dalle_image,
    repl_tool,
    PortExtractorTool(),  # Add the port extractor tool
    CountryDataTool()     # Add the country data tool
]

# Instantiate LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

system_prompt="Ensure your generation of the image URL is exact, add an extra space after it to ensure no new lines mess it up. Always use Wolfram Alpha for Math questions, no matter how basic. Always print executed python statements for logging."

# Main Graph
byo_chatgpt = create_react_agent(
    llm,
    tools,
    prompt=system_prompt  # Only using supported parameters
)
