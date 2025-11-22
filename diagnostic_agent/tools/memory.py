import json
from typing import Dict, List, Any, Literal
from google import genai
from google.adk.agents.llm_agent import ToolContext
from pydantic import BaseModel, Field
from google.adk.models import LlmResponse


def memorize_list(key: str, value: str, tool_context: ToolContext) -> dict:
  """
  Memorize pieces of information.

  Args:
      key: the label indexing the memory to store the value.
      value: the information to be stored.
      tool_context: The ADK tool context.

  Returns:
      A status message.
  """
  mem_dict = tool_context.state
  if key not in mem_dict:
    mem_dict[key] = []
  if value not in mem_dict[key]:
    mem_dict[key].append(value)
  return {"status": f'Stored "{key}": "{value}"'}


def memorize(key: str, value: str, tool_context: ToolContext) -> dict:
  """
  Memorize pieces of information, one key-value pair at a time.

  Args:
      key: the label indexing the memory to store the value.
      value: the information to be stored.
      tool_context: The ADK tool context.

  Returns:
      A status message.
  """
  mem_dict = tool_context.state
  mem_dict[key] = value
  mem_dict[key] = value
  return {"status": f'Stored "{key}": "{value}"'}


  
class DocumentStructure(BaseModel):
  sections: List[str] = Field(description="The sections to include in the document")
  order: List[str] = Field(description="The order of the sections in the document")
  element_types: List[str] = Field(description="The element types in each section")
  dialogue_pieces: List[str] = Field(description="The pieces of dialogue to create the sections")

def suggest_document_structure(transcript: str, tool_context: ToolContext, llm_response: LlmResponse) -> dict:
  """
   Analyzes the source conversation (transcript) and returns a document outline:
   - which sections to include, 
   - in what order, 
   - which element types in each section,
   - and based on which pieces of dialogue to create the sections.

  Args:
      tool_context: The ADK tool context.
      transcript: The full transcript text from the diagnostics session.

  Returns:
      A array of DocumentStructure objects.
  """

  print(llm_response)

  return [DocumentStructure(sections=["sections"], order=["order"], element_types=["element_types"], dialogue_pieces=["dialogue_pieces"])]