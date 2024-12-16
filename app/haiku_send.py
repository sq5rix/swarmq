import marshal

from swarm import Agent, Swarm

from marsh import marshal_object
from rabbit import publish

MODEL = "llama3.2:latest"
client = Swarm()

english_agent_name = "English_Agent"
spanish_agent_name = "Spanish_Agent"

spanish_agent = Agent(
    name=spanish_agent_name,
    model=MODEL,
    instructions="You only speak Spanish.",
)


def transfer_to_spanish_agent():
    """Transfer spanish speaking users immediately."""
    return publish(spanish_agent_name, marshal_object(spanish_agent))


english_agent = Agent(
    name=english_agent_name,
    model=MODEL,
    instructions="You only speak English.",
)

english_agent.functions.append(transfer_to_spanish_agent)

messages = [{"role": "user", "content": "Hola. ¿Como estás?"}]
response = client.run(agent=english_agent, messages=messages)
print("response: ", response)
print(marshal_object(spanish_agent))
