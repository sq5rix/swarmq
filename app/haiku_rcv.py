from swarm import Agent, Swarm

from marsh import unmarshal_object
from rabbit import consume

MODEL = "llama3.2:latest"

client = Swarm()

spanish_agent_name = "Spanish_Agent"


def run_agent(body):
    spanish_agent = unmarshal_object(body)
    print(spanish_agent)
    response = client.run(agent=spanish_agent, messages=["Hola. ¿Como estás?"])

    print(response.messages[-1]["content"])


consume(spanish_agent_name, run_agent)