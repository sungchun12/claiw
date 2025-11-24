from pydantic_ai import Agent
from pydantic_ai.durable_exec.dbos import DBOSAgent
from dbos import DBOS

# @DBOS.step()
def get_weather() -> str:  
    # Your I/O logic here  
    return 'rainy'  

agent = Agent(
    'gpt-5',
    instructions="You're an expert in geography.",
    name='geography',  
    tools=[get_weather],
)

dbos_agent = DBOSAgent(agent)

async def main() -> None:
    # Note: DBOS.launch() would be needed here if running directly with python
    # but we are optimizing for CLI usage now.
    result = await dbos_agent.run('What is the capital of Mexico and tell me the weather?')
    print(result.output)
