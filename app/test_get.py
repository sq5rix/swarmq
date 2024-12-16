import json

from rabbit import consume
from swarm import Agent, Swarm

MODEL = "llama3.2:latest"
client = Swarm()

agent = Agent(
    name="Agent",
    model=MODEL,
    instructions="You are a helpful agent.",
)


def run_agent(message):
    response = client.run(agent=agent, messages=[json.loads(message.decode("utf-8"))])
    print(response.messages[-1]["content"])


consume("Agent", run_agent)
