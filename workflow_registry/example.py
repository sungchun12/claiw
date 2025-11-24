from pydantic_ai import Agent
from pydantic_ai.durable_exec.dbos import DBOSAgent

agent = Agent(
    'gpt-5',
    instructions="You're an expert in geography.",
    name='geography',  
)

dbos_agent = DBOSAgent(agent)  

# Optional: for local testing (won't be used by CLI run)
async def main():
    # Note: DBOS.launch() would be needed here if running directly with python
    # but we are optimizing for CLI usage now.
    result = await dbos_agent.run('What is the capital of Mexico?')  
    print(result.output)
