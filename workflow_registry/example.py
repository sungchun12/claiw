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

@DBOS.step()
async def do_math() -> str:  
    # Your I/O logic here  
    return '1+1=2'

agent = Agent(
    'gpt-5-nano',
    instructions="You're an expert in geography.",
    name='geography',  
    tools=[get_weather],
)

dbos_agent = DBOSAgent(agent)  # the agent is wrapped in a DBOS durable workflow

@DBOS.workflow(name='example')  # this is a workflow that wraps dbos_agent as a nested workflow
async def claiw_handler() -> None:
    # Note: DBOS.launch() would be needed here if running directly with python
    # but we are optimizing for CLI usage now.
    result = await dbos_agent.run('What is the capital of Mexico and the weather?')
    mood = await get_mood()
    math = await do_math()
    print(result.output)
    print(mood)
    print(math)