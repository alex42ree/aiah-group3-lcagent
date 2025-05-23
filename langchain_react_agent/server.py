from fastapi import FastAPI, Body
from langserve import add_routes
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Union, Annotated
from pydantic import BaseModel, create_model
from langchain_react_agent.agent import byo_chatgpt
from langchain_react_agent.country_data import app as country_data_app
from langchain_react_agent.container_data import app as container_data_app

app = FastAPI(
    title="LangChain React Agent",
    version="1.0",
    description="A LangChain agent with React and Hono API integration"
)

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
    input_type=AgentInput
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 