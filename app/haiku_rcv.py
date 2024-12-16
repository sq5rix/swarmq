import json

from swarm import Agent, Swarm

from marsh import unmarshal_object
from rabbit import consume

MODEL = "llama3.2:latest"

client = Swarm()

spanish_agent_name = "Spanish_Agent"

spanish_agent = Agent(
    name=spanish_agent_name,
    model=MODEL,
    instructions="You only speak Spanish.",
)


def run_agent(body):
    print(body)
    response = client.run(
        agent=spanish_agent, messages=json.loads(body.decode("utf-8"))
    )

    print(response.messages[-1]["content"])


consume(spanish_agent_name, run_agent)
