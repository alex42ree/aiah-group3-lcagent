from langchain_community.tools.google_serper import GoogleSerperRun
from langchain_community.utilities.google_serper import GoogleSerperAPIWrapper
from langchain_experimental.utilities import PythonREPL
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool, Tool, BaseTool
from langchain_openai import ChatOpenAI
from openai import OpenAI
from langchain_react_agent.country_data import Operation
from langchain_react_agent.container_data import ContainerType
import requests
import os
import time
import random
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Type, List
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
    llm=llm,
    tools=tools,
    prompt=system_prompt,
    handle_parsing_errors=True
)

# Export the agent for use in the server
__all__ = ["byo_chatgpt"]
