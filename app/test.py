import json

from swarm import Agent, Swarm

from rabbit import publish

MODEL = "llama3.2:latest"
client = Swarm()

agent = Agent(
    name="Agent",
    model=MODEL,
    instructions="You are a helpful agent.",
)

messages = [{"role": "user", "content": "Hi!"}]

publish("Agent", json.dumps(messages[0]))
