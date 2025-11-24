from dbos import DBOS, DBOSConfig

from pydantic_ai import Agent
from pydantic_ai.durable_exec.dbos import DBOSAgent

dbos_config: DBOSConfig = {
    'name': 'example',
    'system_database_url': 'sqlite:///dbostest.sqlite', 
}
DBOS(config=dbos_config)

agent = Agent(
    'gpt-5',
    instructions="You're an expert in geography.",
    name='geography',  
)

dbos_agent = DBOSAgent(agent)  

async def main():
    DBOS.launch()
    result = await dbos_agent.run('What is the capital of Mexico?')  
    print(result.output)
    #> Mexico City (Ciudad de México, CDMX)