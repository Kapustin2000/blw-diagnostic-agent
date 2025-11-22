import sys
import os
import asyncio

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from diagnostic_agent.sub_agents.personal_data_extractor.agent import facts_extractor_agent
from diagnostic_agent.agent import extract_client_facts
from google.adk.agents.llm_agent import ToolContext

async def run_agent_async(agent, transcript):
    print(f"Running agent with transcript: {transcript}")
    # Create a dummy InvocationContext
    from google.adk.agents.llm_agent import InvocationContext
    # We need to pass the input somehow. 
    # InvocationContext has 'user_content' field which might be what we need.
    # Or 'input_realtime_cache'?
    # Let's try to set user_content if it accepts string.
    # But usually input is passed via event or something.
    
    # Actually, let's look at how `run_live` works. It takes parent_context.
    # If we want to pass input, we might need to create a UserContent object.
    
    # Let's try to just pass the context and see if it runs.
    # If it needs input, it might complain or wait.
    
    context = InvocationContext(agent=agent)
    # We can try to inject the input into the context if possible.
    # But maybe we should use `agent.run(transcript)` if we can find a way to run it synchronously or easily.
    
    # Let's try to mock the input by setting it in the context if possible.
    # context.user_content = transcript # user_content might be a list of Content objects.
    
    # Alternative: Use `agent.process_event`?
    
    # Let's try to use `run_live` again but with correct context?
    # No, run_live also takes context.
    
    # Let's try to use `agent.run_async` with a context that has the input.
    # If I can't figure out how to pass input, I might need to look at `Agent.run` implementation again (which I can't read).
    
    # But wait, `extract_client_facts` tool receives `transcript` as string.
    # And it calls `facts_extractor_agent.run(transcript)`.
    # So `run` MUST exist or be dynamically added.
    # But `dir(Agent)` didn't show `run`.
    # Maybe it's added by a decorator or metaclass?
    # Or maybe `extract_client_facts` implementation in my plan was wrong about `run` existing?
    # Yes, I assumed `run` exists.
    
    # If `run` does not exist, I need to implement `extract_client_facts` using `run_live` or `run_async`.
    # And I need to know how to pass the input.
    
    # Let's assume for now I can use `run_async` and pass input via `context`.
    # I will try to set `context.user_content` to the transcript string, although it might expect a list.
    # If that fails, I will try to find another way.
    
    # For the test, let's just try to run it and see what happens.
    
    async for event in agent.run_async(context):
        pass # Consume the generator
    print("Agent run complete.")

def test_facts_extractor_agent():
    print("Testing FactsExtractorAgent directly...")
    transcript = "Client name is John Doe. He is 30 years old. He wants to lose weight."
    
    # We need to run the async generator
    asyncio.run(run_agent_async(facts_extractor_agent, transcript))

    facts = facts_extractor_agent.state.get('facts', [])
    print(f"Extracted facts: {facts}")
    if not facts:
        print("FAILED: No facts extracted.")
    else:
        print("PASSED: Facts extracted.")

def test_extract_client_facts_tool():
    print("\nTesting extract_client_facts tool...")
    transcript = "Client name is Jane Smith. She is 25 years old. She wants to build muscle."
    # Mock ToolContext
    tool_context = ToolContext(agent=None, state={}) 
    
    # extract_client_facts calls run() which we need to fix in agent.py as well
    # But first let's see if we can run it.
    try:
        facts = extract_client_facts(transcript, tool_context)
        print(f"Extracted facts: {facts}")
        if not facts:
            print("FAILED: No facts extracted.")
        else:
            print("PASSED: Facts extracted.")
    except Exception as e:
        print(f"FAILED with error: {e}")

if __name__ == "__main__":
    test_facts_extractor_agent()
    # test_extract_client_facts_tool() # Commented out for now until we fix agent.py
