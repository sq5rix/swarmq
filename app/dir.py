import logging
from typing import Dict, Optional

from swarm import Agent, AgentMessage, Response, Swarm

from models import model_list
from prompts import *
from rabbit import RabbitPublisher

# Initialize SwarmRabbitMQ client
client = Swarm()
rabbit_send = RabbitPublisher("aqueue")

QWEN7 = 2
LLAMA7 = 0
GPT = 10
MODEL = LLAMA7

print("\n=== News Director AI System ===")
print("Type 'quit' to exit\n")


def coordinate_news_flow(topic: str) -> Dict:
    """
    Coordinate the news gathering and publication process
    """
    return {
        "action": "coordinate",
        "steps": [
            {"agent": "NewsGatherer", "task": "research", "query": topic},
            {"agent": "ArticleWriter", "task": "write", "topic": topic},
            {"agent": "Publisher", "task": "publish"},
        ],
    }


news_director = Agent(
    name="NewsDirector",
    model=model_list[MODEL],
    instructions="""You are a News Director responsible for:
    1. Deciding what topics to cover
    2. Coordinating the news gathering and writing process
    3. Ensuring high-quality content
    4. Managing the publication workflow
    
    For each topic:
    1. Send research instructions to NewsGatherer
    2. Forward gathered info to ArticleWriter
    3. Send final article to Publisher
    
    Use clear routing and maintain message flow between agents.""",
    functions=[coordinate_news_flow],
)


def handle_agent_response(response: Optional[Response]) -> bool:
    """Handle agent response and return success status"""
    if not response or not response.last_message:
        logger.error("No response received")
        return False

    print("\nDirector's Response:")
    print("-" * 40)
    print(response.last_message.content)
    print("-" * 40)
    return True


def main():
    # Register only the NewsDirector agent
    client.register_agent(news_director)
    logger.info("NewsDirector registered and started")

    while True:
        try:
            # Get user input
            user_input = input("\nWhat news topic should I cover? > ")

            if user_input.lower() in ["quit", "exit", "q"]:
                print("\nShutting down News Director...")
                break

            # Process the request through NewsDirector
            print("\nProcessing request...")

            # Run the director agent
            response = client.run(
                agent_name="NewsDirector",
                content=user_input,
                metadata={"type": "news_request", "workflow": "start"},
            )

            if response:
                # Director will automatically route messages to other agents
                # via their routing keys (agent names)
                logger.info("News workflow initiated")
            else:
                logger.error("Failed to process news request")

        except KeyboardInterrupt:
            print("\nShutting down News Director...")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            print(f"\nError: {str(e)}")

    # Cleanup
    client.close()


if __name__ == "__main__":
    main()
