from fastapi import FastAPI, Body, HTTPException
from langserve import add_routes
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Union
from pydantic import create_model
from .agent import byo_chatgpt
from .country_data import app as country_data_app
from .container_data import app as container_data_app
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Create FastAPI app
app = FastAPI(
    title="LangChain React Agent",
    version="1.0",
    description="A LangChain agent with React and Hono API integration",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for cloud deployment."""
    return {
        "status": "ok",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "openai_api_key": "configured" if os.getenv("OPENAI_API_KEY") else "missing"
    }

# Mount the apps at different paths
app.mount("/api/country", country_data_app)
app.mount("/api/container", container_data_app)

# Create a simpler input model
AgentInput = create_model(
    "AgentInput",
    messages=(List[Union[HumanMessage, AIMessage]], ...)
)

# Add routes for the agent with proper type definitions
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

# Add error handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """Handle all unhandled exceptions."""
    return {
        "error": str(exc),
        "detail": "An unexpected error occurred",
        "type": type(exc).__name__
    } 