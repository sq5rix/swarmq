import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional

import pika

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def connection_error_handler(func):
    """Decorator to handle connection errors"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"RabbitMQ Connection Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    return wrapper


class RabbitMQ:
    """
    RabbitMQ wrapper class for handling connections and basic operations
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5672,
        virtual_host: str = "/",
        username: str = "guest",
        password: str = "guest",
        connection_attempts: int = 3,
        retry_delay: int = 5,
    ):
        """
        Initialize RabbitMQ connection parameters

        Args:
            host: RabbitMQ server hostname
            port: RabbitMQ server port
            virtual_host: Virtual host to connect to
            username: Authentication username
            password: Authentication password
            connection_attempts: Number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.credentials = pika.PlainCredentials(username, password)
        self.parameters = pika.ConnectionParameters(
            host=host,
            port=port,
            virtual_host=virtual_host,
            credentials=self.credentials,
            connection_attempts=connection_attempts,
            retry_delay=retry_delay,
        )
        self.connection = None
        self.channel = None
        self.connect()

    @connection_error_handler
    def connect(self) -> None:
        """Establish connection to RabbitMQ server"""
        if not self.connection or self.connection.is_closed:
            self.connection = pika.BlockingConnection(self.parameters)
            self.channel = self.connection.channel()
            logger.info("Successfully connected to RabbitMQ")

    def close(self) -> None:
        """Close the RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("RabbitMQ connection closed")

    def __enter__(self):
        """Context manager enter"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class RabbitConsumer(RabbitMQ):
    """
    RabbitMQ Consumer class for message consumption
    """

    def __init__(self, queue_name: str, **kwargs):
        """
        Initialize consumer with queue name and optional connection parameters

        Args:
            queue_name: Name of the queue to consume from
            **kwargs: Additional connection parameters
        """
        super().__init__(**kwargs)
        self.queue_name = queue_name
        self.setup_queue(True)

    @connection_error_handler
    def setup_queue(self, durable: bool = True) -> None:
        """
        Declare the queue for consuming

        Args:
            durable: Whether the queue should survive broker restarts
        """
        self.channel.queue_declare(queue=self.queue_name, durable=durable)

    def consume(self, callback: Callable) -> None:
        """
        Start consuming messages from the queue

        Args:
            callback: Callback function to process received messages
        """

        def wrapped_callback(ch, method, properties, body):
            try:
                callback(body)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=self.queue_name, on_message_callback=wrapped_callback
        )

        logger.info(f"Started consuming from queue: {self.queue_name}")
        self.channel.start_consuming()


class RabbitPublisher(RabbitMQ):
    """
    RabbitMQ Publisher class for message publishing
    """

    def __init__(self, queue_name: str, **kwargs):
        """
        Initialize producer with queue name and optional connection parameters

        Args:
            queue_name: Name of the queue to publish to
            **kwargs: Additional connection parameters
        """
        super().__init__(**kwargs)
        self.queue_name = queue_name
        self.connect()
        self.setup_queue()

    @connection_error_handler
    def setup_queue(self, durable: bool = True) -> None:
        """
        Declare the queue for publishing

        Args:
            durable: Whether the queue should survive broker restarts
        """
        self.channel.queue_declare(queue=self.queue_name, durable=durable)

    def publish(self, message: str) -> None:
        """
        Publish a message to the queue

        Args:
            message: Message to publish
        """
        self.channel.basic_publish(
            exchange="", routing_key=self.queue_name, body=message
        )
        logger.info(f"Published message to queue: {self.queue_name}")
