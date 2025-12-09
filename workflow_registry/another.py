from pydantic_ai import Agent
from pydantic_ai.durable_exec.dbos import DBOSAgent
from dbos import DBOS

@DBOS.step()
async def get_weather() -> str:  
    # Your I/O logic here  
    return 'rainy'  

agent = Agent(
    'gpt-5',
    instructions="You're an expert in geography.",
    name='geography',  
    tools=[get_weather],
)

dbos_agent = DBOSAgent(agent)

@DBOS.workflow(name='another')
async def claiw_handler() -> None:
    # Note: DBOS.launch() would be needed here if running directly with python
    # but we are optimizing for CLI usage now.
    result = await get_weather()
    print(result)
