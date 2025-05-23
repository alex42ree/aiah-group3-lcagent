from fastapi import FastAPI
from langserve import add_routes
from langchain_core.messages import HumanMessage, AIMessage
from typing import Annotated, List, Union
from fastapi import Body
from app.agent import byo_chatgpt
from app.country_data import app as country_data_app
from pydantic import BaseModel

app = FastAPI(
    title="LangChain React Agent",
    version="1.0",
    description="A LangChain agent with React and Hono API integration"
)

# Mount the country data app
app.mount("/api", country_data_app)

# Define the input type for the agent
class AgentInput(BaseModel):
    messages: List[Union[HumanMessage, AIMessage]]

# Add routes for the agent with proper type definitions
add_routes(
    app,
    byo_chatgpt,
    path="/agent",
    enable_feedback_endpoint=True,
    enable_public_trace_link_endpoint=True,
    input_type=Annotated[AgentInput, Body()]  # Use our custom input type
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 