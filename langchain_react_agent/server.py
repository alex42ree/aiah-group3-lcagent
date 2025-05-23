from fastapi import FastAPI, Body, HTTPException
from langserve import add_routes
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Union, Annotated
from pydantic import BaseModel, create_model
from langchain_react_agent.agent import byo_chatgpt
from langchain_react_agent.country_data import app as country_data_app
from langchain_react_agent.container_data import app as container_data_app
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Create FastAPI app with CORS middleware
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
    per_req_config_modifier=lambda config: {
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        proxy_headers=True,
        forwarded_allow_ips="*"
    ) 