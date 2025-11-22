import os
import warnings
import logging
from pathlib import Path
from google.adk.agents.llm_agent import Agent
from .tools.memory import suggest_document_structure

from .sub_agents.client_portrait_agent.agent import client_portrait_agent
from google.adk.tools.agent_tool import AgentTool

from .sub_agents.doc_structure_planner.agent import doc_structure_planner_agent
from .tools.docx_creator import create_docx_from_structure

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, environment variables should be set manually
    pass

# Suppress warnings from Google ADK about non-text parts and API keys
warnings.filterwarnings('ignore', message='.*non-text parts.*')
warnings.filterwarnings('ignore', message='.*Both GOOGLE_API_KEY and GEMINI_API_KEY.*')
warnings.filterwarnings('ignore', message='.*Default value is not supported.*')

# Suppress logging from google libraries
logging.getLogger('google').setLevel(logging.ERROR)
logging.getLogger('google.genai').setLevel(logging.ERROR)
logging.getLogger('google.adk').setLevel(logging.ERROR)

# Load instructions from instructions.md file
_instructions_path = Path(__file__).parent / "instructions.md"
with open(_instructions_path, "r", encoding="utf-8") as f:
    _agent_instructions = f.read()

# ADK will automatically use environment variables:
# - GEMINI_API_KEY for Google AI API
# - GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION for Vertex AI
# Make sure one of these is set in your .env file or environment

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A helpful assistant that analyzes client diagnostics and helps create a comprehensive diagnostic report.',
    instruction=_agent_instructions,
    tools=[
        AgentTool(client_portrait_agent),
        AgentTool(doc_structure_planner_agent),
        create_docx_from_structure,
    ],
)
