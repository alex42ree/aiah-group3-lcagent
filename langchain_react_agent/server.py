from fastapi import FastAPI, Body, HTTPException
from langserve import add_routes
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Union
from pydantic import create_model
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to the Python path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.append(str(parent_dir))

# Load environment variables
load_dotenv(override=True)

try:
    from langchain_react_agent.agent import byo_chatgpt
    from langchain_react_agent.country_data import app as country_data_app
    from langchain_react_agent.container_data import app as container_data_app
except ImportError as e:
    print(f"Error importing modules: {e}")
    print(f"Current sys.path: {sys.path}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Looking for modules in: {current_dir}")
    raise

# Create FastAPI app
app = FastAPI(
    title="LangChain React Agent",
    version="1.0",
    description="A LangChain agent with React and Hono API integration",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add health check endpoint with more detailed information
@app.get("/health")
async def health_check():
    """Health check endpoint for cloud deployment."""
    return {
        "status": "ok",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "openai_api_key": "configured" if os.getenv("OPENAI_API_KEY") else "missing",
        "python_path": sys.path,
        "current_directory": os.getcwd(),
        "module_location": str(current_dir)
    }

# Mount the apps at different paths
try:
    app.mount("/api/country", country_data_app)
    app.mount("/api/container", container_data_app)
except Exception as e:
    print(f"Error mounting apps: {e}")
    raise

# Create a simpler input model
AgentInput = create_model(
    "AgentInput",
    messages=(List[Union[HumanMessage, AIMessage]], ...)
)

# Add routes for the agent with proper type definitions
try:
    add_routes(
        app,
        byo_chatgpt,
        path="/agent",
        enable_feedback_endpoint=True,
        enable_public_trace_link_endpoint=True,
        input_type=AgentInput,
        per_req_config_modifier=lambda config, request: {
            **config,
            "configurable": {
                **config.get("configurable", {}),
                "openai_api_key": os.getenv("OPENAI_API_KEY")
            }
        }
    )
except Exception as e:
    print(f"Error adding routes: {e}")
    raise

# Add error handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """Handle all unhandled exceptions."""
    return {
        "error": str(exc),
        "detail": "An unexpected error occurred",
        "type": type(exc).__name__,
        "python_path": sys.path,
        "current_directory": os.getcwd()
    } 