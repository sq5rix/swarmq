import json

from rabbit import publish
from swarm import Agent, Swarm

MODEL = "llama3.2:latest"
client = Swarm()

agent = Agent(
    name="Agent",
    model=MODEL,
    instructions="You are a helpful agent.",
)

messages = [{"role": "user", "content": "Hi!"}]

publish("Agent", json.dumps(message[0]))
