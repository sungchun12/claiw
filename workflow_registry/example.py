from pydantic_ai import Agent
from pydantic_ai.durable_exec.dbos import DBOSAgent
from dbos import DBOS

@DBOS.step()
async def get_weather() -> str:  
    # Your I/O logic here  
    return 'It is sunny today'

@DBOS.step()
async def get_mood() -> str:  
    # Your I/O logic here  
    return 'You are happy today'

agent = Agent(
    'gpt-5-nano',
    instructions="You're an expert in geography.",
    name='geography',  
    tools=[get_weather],
)

dbos_agent = DBOSAgent(agent)  

@DBOS.workflow() # this is a workflow that wraps dbos_agent as a nested workflow
async def main() -> None:
    # Note: DBOS.launch() would be needed here if running directly with python
    # but we are optimizing for CLI usage now.
    result = await dbos_agent.run('What is the capital of Mexico and the weather?')
    mood = await get_mood()
    print(result.output)
    print(mood)
