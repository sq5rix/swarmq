import pickle
from typing import Callable, List

from swarm import Agent


# Function to marshal the object
def marshal_object(obj: Agent) -> bytes:
    """
    Serialize the object to a byte stream using pickle.

    :param obj: The ComplexObject to serialize
    :return: Serialized byte stream
    """
    return pickle.dumps(obj)


# Function to unmarshal the object
def unmarshal_object(serialized_obj: bytes) -> Agent:
    """
    Deserialize the object from a byte stream using pickle.

    :param serialized_obj: Serialized byte stream
    :return: Deserialized ComplexObject
    """
    return pickle.loads(serialized_obj)


def main():

    MODEL = "llama3.2:latest"

    english_agent_name = "English_Agent"
    spanish_agent_name = "Spanish_Agent"

    spanish_agent = Agent(
        name=spanish_agent_name,
        model=MODEL,
        instructions="You only speak Spanish.",
    )

    def transfer_to_spanish_agent():
        """Transfer spanish speaking users immediately."""
        print(marshal_object(spanish_agent))
        return publish(spanish_agent_name, marshal_object(spanish_agent))

    english_agent = Agent(
        name=english_agent_name,
        model=MODEL,
        instructions="You only speak English.",
    )
    english_agent.functions.append(transfer_to_spanish_agent)

    obj = marshal_object(english_agent)

    print(obj)
    print(type(obj))


if __name__ == "__main__":
    main()
