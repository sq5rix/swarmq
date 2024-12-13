import unittest
from unittest.mock import MagicMock, patch
import pika
from your_module import RabbitMQ, RabbitConsumer


class TestRabbitMQ(unittest.TestCase):
    def setUp(self):
        self.rabbit = RabbitMQ()

    @patch("pika.BlockingConnection")
    def test_connect(self, mock_connection):
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel

        self.rabbit.connect()

        mock_connection.assert_called_once()
        self.assertIsNotNone(self.rabbit.connection)
        self.assertIsNotNone(self.rabbit.channel)

    def test_context_manager(self):
        with patch("pika.BlockingConnection") as mock_connection:
            mock_channel = MagicMock()
            mock_connection.return_value.channel.return_value = mock_channel

            with RabbitMQ() as rabbit:
                self.assertIsNotNone(rabbit.connection)
                self.assertIsNotNone(rabbit.channel)


class TestRabbitConsumer(unittest.TestCase):
    def setUp(self):
        self.consumer = RabbitConsumer(queue_name="test_queue")

    @patch("pika.BlockingConnection")
    def test_setup_queue(self, mock_connection):
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel

        self.consumer.connect()
        self.consumer.setup_queue()

        mock_channel.queue_declare.assert_called_once_with(
            queue="test_queue", durable=True
        )


if __name__ == "__main__":
    unittest.main()
