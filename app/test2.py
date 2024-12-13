import json
import threading
import time

from swarm import Agent, SwarmRabbitMQ


def message_handler(message):
    """Handle received messages"""
    print("\n=== Message Received ===")
    print(f"Content: {json.dumps(message, indent=2)}")

    # You can add specific handling based on message type
    if "messages" in message:
        for msg in message["messages"]:
            if msg["role"] == "user":
                print(f"\nProcessing user message: {msg['content']}")
                # Add your messag be processing logic here

    if "context_variables" in message:
        print(
            f"\nContext variables: {json.dumps(message['context_variables'], indent=2)}"
        )


def start_consumer_for_agent(client, agent):
    """Start a consumer thread for an agent"""
    max_retries = 3
    retry_count = 0

    def create_new_connection():
        """Create a fresh connection for the consumer"""
        new_client = SwarmRabbitMQ(rabbitmq_config=rabbitmq_config)
        new_client.register_agent(agent)
        return new_client

    while retry_count < max_retries:
        try:
            print(f"\n[INFO] Starting consumer for {agent.name}")
            # Create a new connection for this consumer
            consumer_client = create_new_connection()
            consumer_client.start_consuming(agent, callback=message_handler)
            break
        except Exception as e:
            retry_count += 1
            print(f"[ERROR] Consumer error for {agent.name}: {str(e)}")
            if retry_count < max_retries:
                wait_time = retry_count * 5  # Exponential backoff
                print(
                    f"[INFO] Retry {retry_count}/{max_retries} for {agent.name} in {wait_time} seconds..."
                )
                time.sleep(wait_time)
                # Clean up the failed connection
                try:
                    del consumer_client
                except:
                    pass
            else:
                print(f"[ERROR] Max retries reached for {agent.name}")
                break


# RabbitMQ configuration
rabbitmq_config = {
    "host": "localhost",
    "port": 5672,
    "username": "guest",
    "password": "guest",
}

try:
    # Initialize SwarmRabbitMQ
    client = SwarmRabbitMQ(rabbitmq_config=rabbitmq_config)

    # Create test agents
    agent_a = Agent(name="Agent A", role="Sender")
    agent_b = Agent(name="Agent B", role="Receiver")

    # Register agents
    client.register_agent(agent_a)
    client.register_agent(agent_b)

    # Start consumers in separate threads
    consumer_threads = []
    for agent in [agent_a, agent_b]:
        consumer_thread = threading.Thread(
            target=start_consumer_for_agent,
            args=(client, agent),
            daemon=True,
            name=f"Consumer-{agent.name}",  # Named threads for better debugging
        )
        consumer_threads.append(consumer_thread)
        consumer_thread.start()

    # Wait for consumers to start and verify they're running
    time.sleep(2)  # Give more time for consumers to initialize

    # Check if consumers are alive
    alive_consumers = [t for t in consumer_threads if t.is_alive()]
    if len(alive_consumers) != len(consumer_threads):
        print("[WARNING] Not all consumers started successfully")

    # Send test messages
    test_messages = [{"role": "user", "content": "I want to talk to agent B."}]

    # Test context variables
    context = {"conversation_id": "test_123", "timestamp": time.time()}

    # Run the test
    print("\n=== Sending Messages ===")
    try:
        response = client.run(agent_a, test_messages, context_variables=context)
        # Convert Response object to serializable dictionary
        serializable_response = {
            "agent": str(getattr(response, "agent", "")),
            "status": "queued",
            "message_count": len(test_messages),
            "final_message": str(getattr(response, "final_message", "")),
            "context": context,
        }
        print(f"Run response: {json.dumps(serializable_response, indent=2)}")
    except Exception as e:
        print(f"[ERROR] Failed to process response: {str(e)}")

    try:
        # Send a handoff message
        handoff_response = client.handoff_to_agent(
            agent_a, agent_b, test_messages, context
        )
        print(f"Handoff response: {json.dumps(handoff_response, indent=2)}")
    except Exception as e:
        print(f"[ERROR] Failed to handoff: {str(e)}")

    # Keep main thread alive to see messages being processed
    max_monitor_time = 30  # Maximum monitoring time in seconds
    start_time = time.time()

    try:
        while time.time() - start_time < max_monitor_time:
            try:
                # Get queue status
                queue_status = client.debug_queues()
                print("\nCurrent queue status:")
                print(json.dumps(queue_status, indent=2))

                # Check if all messages are processed
                total_messages = sum(
                    q.get("message_count", 0) for q in queue_status.values()
                )
                if total_messages == 0:
                    print("\nAll messages processed!")
                    break

                time.sleep(5)  # Wait 5 seconds before next status check
            except Exception as e:
                print(f"[ERROR] Failed to get queue status: {str(e)}")
                time.sleep(5)
        else:
            print("\n[WARNING] Monitoring timeout reached")

    except KeyboardInterrupt:
        print("\nShutting down...")
    except KeyboardInterrupt:
        print("\nShutting down...")

except Exception as e:
    print(f"Error: {str(e)}")
finally:
    if "client" in locals():
        del client  # Ensure proper cleanup
