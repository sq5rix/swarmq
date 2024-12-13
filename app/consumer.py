import json
import time

from rabbit import RabbitConsumer


def callback(message):
    print(f" [x] Received: {message}")


# Create Rabbit instance and start consuming
rabbit = RabbitConsumer("aqueue")
rabbit.consume(callback)

print(" [*] Waiting for messages. To exit press CTRL+C")
