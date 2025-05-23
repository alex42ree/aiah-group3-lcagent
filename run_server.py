"""Entry point script for running the LangChain React Agent server."""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"Starting server on {host}:{port}")
    print("Environment variables loaded:")
    print(f"OPENAI_API_KEY: {'configured' if os.getenv('OPENAI_API_KEY') else 'missing'}")
    print(f"ENVIRONMENT: {os.getenv('ENVIRONMENT', 'development')}")
    
    uvicorn.run(
        "langchain_react_agent.server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
        proxy_headers=True,
        forwarded_allow_ips="*"
    ) 