import logging
import time
from typing import Optional

from duck import search_news
from models import model_list
from prompts import *

from swarm import Agent, AgentMessage, RabbitMQConfig, SwarmRabbitMQ

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("NewsAgents")

# Initialize SwarmRabbitMQ client with explicit config
client = SwarmRabbitMQ(
    config=RabbitMQConfig(
        host="localhost",
        port=5672,
        username="guest",
        password="guest",
        virtual_host="/",  # Explicitly set the virtual host
    )
)

# Model constants
QWEN7 = 2
LLAMA7 = 0
GPT = 10
MODEL = LLAMA7


# Define function to wrap search_news for agent use
def agent_search_news(**kwargs) -> dict:
    """Wrapper for search_news to work with agent messaging"""
    results = search_news(**kwargs)
    return {"status": "success", "results": results}


# Define the worker agents with new RabbitMQ-aware configuration
news_gatherer = Agent(
    name="NewsGatherer",
    model=model_list[MODEL],
    instructions="""You are a News Researcher who:
    1. Takes a topic or query
    2. Uses the search_news function to gather relevant information
    3. Analyzes and summarizes the findings
    4. Provides structured data for the article writer
    
    Always verify sources and collect multiple perspectives.""",
    functions=[agent_search_news],
)

article_writer = Agent(
    name="ArticleWriter",
    model=model_list[MODEL],
    instructions="""You are a Professional Writer who:
    1. Takes researched information
    2. Creates engaging, well-structured articles
    3. Maintains journalistic standards
    4. Produces SEO-friendly content
    
    Write in AP style and ensure factual accuracy.""",
)

publisher = Agent(
    name="Publisher",
    model=model_list[MODEL],
    instructions="""You are a Content Publisher who:
    1. Takes the final article
    2. Formats it for WordPress
    3. Adds appropriate tags and categories
    4. Handles the publication process
    
    Ensure proper formatting and metadata.""",
)

# Register agents with the client
logger.info("Registering agents...")
client.register_agent(news_gatherer)
logger.info(f"Agent {news_gatherer.name} registered")
client.register_agent(article_writer)
logger.info(f"Agent {article_writer.name} registered")
client.register_agent(publisher)
logger.info(f"Agent {publisher.name} registered")


def process_agent_message(agent_name: str, message: AgentMessage) -> Optional[str]:
    """Process a message for a specific agent"""
    try:
        logger.info(f"Processing message for {agent_name}")
        logger.debug(f"Message content: {message.content[:200]}...")

        # Run the agent with the message
        response = client.run(
            agent_name=agent_name, content=message.content, metadata=message.metadata
        )

        if response and response.last_message:
            logger.info(f"Got response from {agent_name}")
            return response.last_message.content

        return None

    except Exception as e:
        logger.error(f"Error processing message for {agent_name}: {e}")
        return None


def handle_news_flow(query: str):
    """Handle the complete news article generation flow"""
    try:
        # Step 1: News Gathering
        gather_response = process_agent_message(
            "NewsGatherer",
            AgentMessage(
                content=query, sender="system", metadata={"type": "news_query"}
            ),
        )

        if not gather_response:
            raise Exception("Failed to gather news")

        # Step 2: Article Writing
        write_response = process_agent_message(
            "ArticleWriter",
            AgentMessage(
                content=gather_response,
                sender="NewsGatherer",
                metadata={"type": "article_content"},
            ),
        )

        if not write_response:
            raise Exception("Failed to write article")

        # Step 3: Publishing
        publish_response = process_agent_message(
            "Publisher",
            AgentMessage(
                content=write_response,
                sender="ArticleWriter",
                metadata={"type": "publish_content"},
            ),
        )

        return publish_response

    except Exception as e:
        logger.error(f"Error in news flow: {e}")
        return None


if __name__ == "__main__":
    print("\nStarting News Agents System...")
    print("Waiting for tasks. Press Ctrl+C to exit.\n")

    try:
        # Register and start all agents
        for agent in [news_gatherer, article_writer, publisher]:
            client.register_agent(agent)
            logger.info(f"Agent {agent.name} registered and started")

        # Example news flow
        test_query = "Latest developments in AI"
        result = handle_news_flow(test_query)

        if result:
            print("\nNews Flow Complete!")
            print("=" * 50)
            print(result[:200])
            print("=" * 50)

        # Keep the main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down news agents...")
        client.close()
