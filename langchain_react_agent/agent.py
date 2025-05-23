from langchain_community.tools.google_serper import GoogleSerperRun
from langchain_community.utilities.google_serper import GoogleSerperAPIWrapper
from langchain_experimental.utilities import PythonREPL
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool, Tool, BaseTool
from langchain_openai import ChatOpenAI
from openai import OpenAI
from langchain_react_agent.country_data import Operation  # Updated import
from langchain_react_agent.container_data import ContainerType  # Updated import
import requests
import os
import time
import random
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Type, List
from dotenv import load_dotenv
import json
from urllib.parse import urljoin

# Load environment variables
load_dotenv()

# Get the base URL for the API
API_BASE_URL = os.getenv('API_BASE_URL', 'http://127.0.0.1:8000')
COUNTRY_DATA_ENDPOINT = urljoin(API_BASE_URL, '/api/country/country-data')
CONTAINER_CHECK_ENDPOINT = urljoin(API_BASE_URL, '/api/container/container-check')

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


class CountryDataInput(BaseModel):
    """Input for the country data tool."""
    operation: Operation = Field(description="The operation to perform: 'get_entry', 'search', or 'same_country'")
    entry_id: Optional[str] = Field(default=None, description="The ID of the entry to get")
    search_query: Optional[str] = Field(default=None, description="The search query for finding entries")
    entry1_id: Optional[str] = Field(default=None, description="First entry ID for same_country check")
    entry2_id: Optional[str] = Field(default=None, description="Second entry ID for same_country check")

class CountryDataTool(BaseTool):
    name: str = "country_data"
    description: str = """Use this tool to get information about countries and cities.
    You can:
    1. Get a single entry by ID (e.g., 'DE-HAM', 'US-NYC')
    2. Search for entries by name or country
    3. Check if two entries are in the same country

    Examples:
    - To get info about Hamburg: "Get information about DE-HAM"
    - To search for cities: "Search for Hamburg"
    - To check if cities are in same country: "Are DE-HAM and DE-HRB in the same country?"

    Note: When an exact ID (like 'DE-HAM') is provided, use the get_entry operation.
    """
    args_schema: Type[BaseModel] = CountryDataInput

    def _run(self, operation: str, entry_id: Optional[str] = None, search_query: Optional[str] = None,
             entry1_id: Optional[str] = None, entry2_id: Optional[str] = None) -> str:
        """Run the tool."""
        # If entry_id contains a hyphen, it's likely an exact ID, so use get_entry
        if entry_id and '-' in entry_id:
            operation = Operation.GET_ENTRY
        else:
            # Convert string operation to enum
            try:
                operation = Operation(operation)
            except ValueError:
                return f"Error: Invalid operation '{operation}'. Must be one of: {', '.join(op.value for op in Operation)}"

        # Prepare the request payload based on operation
        payload = {"operation": operation.value}  # Use .value to get the string value
        
        if operation == Operation.GET_ENTRY:
            if not entry_id:
                return "Error: entry_id is required for get_entry operation"
            payload["entry_id"] = entry_id
        elif operation == Operation.SEARCH:
            if not search_query:
                return "Error: search_query is required for search operation"
            payload["search_query"] = search_query
        elif operation == Operation.SAME_COUNTRY:
            if not entry1_id or not entry2_id:
                return "Error: Both entry1_id and entry2_id are required for same_country operation"
            payload["entry1_id"] = entry1_id
            payload["entry2_id"] = entry2_id

        print(f"Sending request to API: {json.dumps(payload, indent=2)}")
        print(f"API URL: {COUNTRY_DATA_ENDPOINT}")
        
        try:
            # Use the FastAPI endpoint
            response = requests.post(
                COUNTRY_DATA_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # Log the response status and headers
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                print(f"Error response body: {response.text}")
                response.raise_for_status()
                
            result = response.json()
            print(f"API Response: {json.dumps(result, indent=2)}")
            return json.dumps(result["data"], indent=2)
        except requests.exceptions.RequestException as e:
            print(f"API Error: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Error response status: {e.response.status_code}")
                print(f"Error response headers: {dict(e.response.headers)}")
                print(f"Error response body: {e.response.text}")
                if hasattr(e.response, 'json'):
                    error_detail = e.response.json().get('detail', str(e))
                else:
                    error_detail = e.response.text
            else:
                error_detail = str(e)
            return f"Error: {error_detail}"

class ContainerCount(BaseModel):
    """Container count input."""
    type: ContainerType = Field(description="The type of container (HH42, HH24, or HH12)")
    count: int = Field(ge=0, description="Number of containers (must be >= 0)")

class ContainerCheckInput(BaseModel):
    """Input for the container check tool."""
    containers: List[ContainerCount] = Field(description="List of container counts to check")

class ContainerCheckTool(BaseTool):
    name: str = "container_check"
    description: str = """Use this tool to validate container configurations.
    You can check if a container configuration is valid by providing counts for different container types.
    
    The tool validates:
    1. Container types must be one of: HH42, HH24, HH12
    2. Container counts must be >= 0
    3. At least one container type must have a count > 0
    
    Examples:
    - "Check if we have 2 HH42 containers and 1 HH24 container"
    - "Validate container configuration: 3 HH42, 0 HH24, 1 HH12"
    - "Are these containers valid: 0 HH42, 0 HH24, 0 HH12" (this will return an error)
    """
    args_schema: Type[BaseModel] = ContainerCheckInput

    def _run(self, containers: List[ContainerCount]) -> str:
        """Run the tool."""
        # Prepare the request payload
        payload = {
            "containers": [
                {"type": container.type.value, "count": container.count}
                for container in containers
            ]
        }

        print(f"Sending request to API: {json.dumps(payload, indent=2)}")
        print(f"API URL: {CONTAINER_CHECK_ENDPOINT}")
        
        try:
            # Use the FastAPI endpoint
            response = requests.post(
                CONTAINER_CHECK_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # Log the response status and headers
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                print(f"Error response body: {response.text}")
                response.raise_for_status()
                
            result = response.json()
            print(f"API Response: {json.dumps(result, indent=2)}")
            return json.dumps(result["data"], indent=2)
        except requests.exceptions.RequestException as e:
            print(f"API Error: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Error response status: {e.response.status_code}")
                print(f"Error response headers: {dict(e.response.headers)}")
                print(f"Error response body: {e.response.text}")
                if hasattr(e.response, 'json'):
                    error_detail = e.response.json().get('detail', str(e))
                else:
                    error_detail = e.response.text
            else:
                error_detail = str(e)
            return f"Error: {error_detail}"

# Define list of tools
tools = [
    #wolfram_alpha_llm_api,
    #web_search,
    CountryDataTool(),     # Add the country data tool
    ContainerCheckTool()   # Add the container check tool
]

# Instantiate LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

system_prompt="Collect information about the origin port and the destination port. Use the country_data tool to validate the information or to search for the port codes if not provided. Assure that the origin and the destionation port are NOT in the same country. If yes, ask the user to provide the port codes again. Check the number of containers of different types (HH42, HH24, HH12). There must be at least 1 container given in one category. Use the container check tool to check the number and type of containers. If the type is wrong or the number is not at least 1 ask the user to provide the correct container information. "

# Main Graph
byo_chatgpt = create_react_agent(
    llm,
    tools,
    prompt=system_prompt  # Only using supported parameters
)
