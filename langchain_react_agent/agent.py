from langchain_community.tools.google_serper import GoogleSerperRun
from langchain_community.utilities.google_serper import GoogleSerperAPIWrapper
from langchain_experimental.utilities import PythonREPL
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool, Tool, BaseTool
from langchain_openai import ChatOpenAI
from openai import OpenAI
from .country_data import Operation, CountryDataRequest, SameCountryRequest, GetEntryRequest, SearchRequest
from .container_data import ContainerType, ContainerRequest
import requests
import os
import time
import random
from pydantic import BaseModel, Field, RootModel
from typing import Optional, Dict, Any, Type, List, Union, Literal
from dotenv import load_dotenv
import json
from urllib.parse import urljoin

# Load environment variables with override
load_dotenv(override=True)

# Initialize environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Get the base URL for the API - use environment variable or default to relative path
API_BASE_URL = os.getenv('API_BASE_URL', '')
if not API_BASE_URL:
    # In cloud environment, use relative paths
    COUNTRY_DATA_ENDPOINT = '/api/country/country-data'
    CONTAINER_CHECK_ENDPOINT = '/api/container/container-check'
else:
    # In local environment, use full URLs
    COUNTRY_DATA_ENDPOINT = urljoin(API_BASE_URL, '/api/country/country-data')
    CONTAINER_CHECK_ENDPOINT = urljoin(API_BASE_URL, '/api/container/container-check')

# Debug: Print environment variables (masked for security)
print("\nDebug: Environment Variables:")
print(f"OPENAI_API_KEY exists: {'Yes' if OPENAI_API_KEY else 'No'}")
print(f"API_BASE_URL: {API_BASE_URL or 'Using relative paths'}\n")

# Add these new models at the top level, before the CountryDataTool class
class WrappedRequest(BaseModel):
    root: Union[GetEntryRequest, SearchRequest, SameCountryRequest]

class CountryDataTool(BaseTool):
    name: str = "country_data"
    description: str = """Use this tool to validate port information or search for port codes.
    Input should be a JSON object with:
    - operation: One of 'get_entry', 'search', or 'same_country'
    - For get_entry: entry_id (required)
    - For search: search_query (required)
    - For same_country: entry1_id and entry2_id (both required)
    """
    args_schema: Type[BaseModel] = WrappedRequest

    def _run(self, request: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Run the tool."""
        try:
            # Parse the input into our WrappedRequest model
            if isinstance(request, str):
                request_data = json.loads(request)
            elif isinstance(request, dict):
                if 'args' in request:
                    request_data = request['args']
                elif 'function' in request and 'arguments' in request['function']:
                    request_data = json.loads(request['function']['arguments'])
                else:
                    request_data = request
            else:
                raise ValueError(f"Unexpected request type: {type(request)}")

            # Validate and parse the request using our WrappedRequest model
            wrapped_request = WrappedRequest.model_validate(request_data)
            request_obj = wrapped_request.root

            # Send the request to the API
            response = requests.post(
                COUNTRY_DATA_ENDPOINT,
                json=request_obj.model_dump(),
                verify=bool(API_BASE_URL)  # Only verify SSL in local environment
            )
            response.raise_for_status()
            return response.json()
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON format: {str(e)}"}
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Validation error: {str(e)}"}

class ContainerCheckTool(BaseTool):
    name: str = "container_check"
    description: str = """Use this tool to validate container configurations.
    Input should be a JSON object with a list of containers, each having:
    - type: One of 'HH42', 'HH24', or 'HH12'
    - count: Number of containers (must be >= 0)
    At least one container type must have a count greater than 0.
    """
    args_schema: Type[BaseModel] = ContainerRequest

    def _run(self, request: ContainerRequest) -> Dict[str, Any]:
        """Run the tool."""
        try:
            response = requests.post(
                CONTAINER_CHECK_ENDPOINT,
                json=request.model_dump(),
                verify=bool(API_BASE_URL)  # Only verify SSL in local environment
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

# Initialize LLM with explicit API key
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
    api_key=OPENAI_API_KEY
)

# Define list of tools
tools = [
    CountryDataTool(),
    ContainerCheckTool()
]

system_prompt = """Collect information about the origin port and the destination port. 
Use the country_data tool to validate the information or to search for the port codes if not provided. 
Assure that the origin and the destination port are NOT in the same country. 
If yes, ask the user to provide the port codes again. 
Check the number of containers of different types (HH42, HH24, HH12). 
There must be at least 1 container given in one category. 
Use the container check tool to check the number and type of containers. 
If the type is wrong or the number is not at least 1 ask the user to provide the correct container information."""

# Create the agent with explicit configuration
byo_chatgpt = create_react_agent(
    llm,
    tools,
    prompt=system_prompt
)

# Export the agent for use in the server
__all__ = ["byo_chatgpt"]
