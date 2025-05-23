# LangChain React Agent

A LangChain agent with React and Hono API integration for port and container validation.

## Installation

```bash
# Install in development mode
pip install -e .
```

## Project Structure

```
langchain-react-agent/
├── setup.py                 # Package setup and dependencies
├── README.md               # This file
├── requirements.txt        # Development dependencies
├── pyproject.toml         # Python project configuration
└── langchain_react_agent/  # Main package directory
    ├── __init__.py        # Package initialization
    ├── agent.py           # Main agent implementation
    ├── server.py          # FastAPI server implementation
    ├── country_data.py    # Country and port data handling
    └── container_data.py  # Container validation logic
```

## Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -e .
```

3. Run the server:
```bash
python run_server.py
```

## Environment Variables

Create a `.env` file with:
```
OPENAI_API_KEY=your_api_key_here
API_BASE_URL=your_base_url_here  # Optional
```

## License

MIT License
