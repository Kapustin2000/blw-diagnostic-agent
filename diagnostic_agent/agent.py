from pathlib import Path
from google.adk.agents.llm_agent import Agent
from .tools.memory import suggest_document_structure

from .sub_agents.client_portrait_agent.agent import client_portrait_agent
from google.adk.tools.agent_tool import AgentTool

from .sub_agents.doc_structure_planner.agent import doc_structure_planner_agent
from .tools.docx_creator import create_docx_from_structure


# Load instructions from instructions.md file
_instructions_path = Path(__file__).parent / "instructions.md"
with open(_instructions_path, "r", encoding="utf-8") as f:
    _agent_instructions = f.read()

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
