from google.adk.agents.llm_agent import Agent, CallbackContext
from google.adk.models import LlmResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
import json

class DocElement(BaseModel):
    type: Literal['p', 'ul', 'li', 'table', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'] = Field(description="The type of the HTML element.")
    content: str = Field(description="The content of the element. For tables, this should be a markdown table string.")

class Subsection(BaseModel):
    title: str = Field(description="The title of the subsection.")
    elements: List[DocElement] = Field(description="The elements within the subsection.")

class Section(BaseModel):
    title: str = Field(description="The title of the section.")
    description: Optional[str] = Field(default=None, description="An optional brief description of what this section covers.")
    conclusion: Optional[str] = Field(default=None, description="An optional conclusion or summary for this section.")
    elements: List[DocElement] = Field(default_factory=list, description="Elements directly in the section (preferred). Use tables extensively for structured data.")
    subsections: Optional[List[Subsection]] = Field(default=None, description="Optional subsections. Prefer using elements directly in sections instead.")

class DocStructure(BaseModel):
    sections: List[Section] = Field(description="The sections of the document.")

def save_doc_structure_callback(callback_context: CallbackContext, llm_response: LlmResponse):
    """
    Callback to save the planned document structure from the LLM response.
    """
    if llm_response and llm_response.content and llm_response.content.parts:
        try:
            # Extract text from all text parts, ignoring non-text parts (thought_signature, function_call, etc.)
            text_parts = []
            for part in llm_response.content.parts:
                if hasattr(part, 'text') and part.text:
                    text_parts.append(part.text)
            
            if not text_parts:
                print("ERROR: No text parts found in response")
                return
            
            # Combine all text parts
            text_response = '\n'.join(text_parts)
            
            # Clean up potential markdown code blocks
            if text_response.startswith("```json"):
                text_response = text_response.replace("```json", "").replace("```", "").strip()
            elif text_response.startswith("```"):
                text_response = text_response.replace("```", "").strip()
            
            structure_dict = json.loads(text_response)
            # We can validate/parse it into the model to ensure it's correct, then dump it back or store as dict
            doc_structure = DocStructure(**structure_dict)
            callback_context.state['doc_structure'] = doc_structure.model_dump()
            # Only print if verbose mode is enabled (removed debug output)
        except Exception as e:
            print(f"ERROR: Failed to parse or save doc structure: {e}")

doc_structure_planner_agent = Agent(
    model='gemini-2.5-flash',
    name='doc_structure_planner_agent',
    description='Plans the structure of a diagnostic document based on personal data.',
    instruction='''You are an expert document planner. Analyze the provided personal data and create a detailed structure for a diagnostic document.

IMPORTANT GUIDELINES:
- Prefer placing elements directly in sections rather than using subsections
- Use tables extensively for structured data: personal info, medical history, test results, physical assessment findings, recommendations
- Tables should be formatted as markdown tables with headers
- Only use subsections when absolutely necessary for complex hierarchical organization
- Each section should have a clear title and can include description/conclusion if needed
- Use paragraph elements for narrative text, tables for structured data, lists for bullet points

<personal_data>
{personal_data}
</personal_data>

The document should be comprehensive and tailored to the client's needs based on the facts.''',
    output_schema=DocStructure,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    after_model_callback=[save_doc_structure_callback]
)
